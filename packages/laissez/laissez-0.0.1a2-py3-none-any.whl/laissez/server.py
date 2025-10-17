"""
==========
LAISSEZ
==========
"""

import asyncio
import base64
import json
from fastmcp import FastMCP
from fastmcp.server.http import StarletteWithLifespan
from eth_account import Account
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, cast
from starlette.responses import JSONResponse
from starlette.types import Message, Receive, Scope, Send
from x402.facilitator import FacilitatorClient
from x402.common import find_matching_payment_requirements, process_price_to_atomic_amount, x402_VERSION
from x402.types import PaymentPayload, PaymentRequirements, x402PaymentRequiredResponse, SupportedNetworks
from laissez.common import check_and_create_wallet


class PaidTool(BaseModel):
    """
    Configure a paid tool for an MCP server.

    Args:
        name: The name of the tool
        price: The price of the tool in USDC. Defaults to 0.001.
        network: The network to use for the tool. Defaults to 'base-sepolia'.
        description: The description of the tool
    """
    name: str = Field(..., description="The name of the tool")
    price: float = Field(0.001, description="The price of the tool in USDC")
    network: Optional[Literal['base-sepolia', 'base']] = Field('base-sepolia', description="The network to use for the tool")
    description: str = Field(..., description="The description of the tool")



class RequestReplay:
    def __init__(self, receive: Receive, body: bytes):
        self._receive = receive
        self._body = body
        self._called = False

    async def __call__(self) -> Message:
        if not self._called:
            self._called = True
            return {"type": "http.request", "body": self._body, "more_body": False}
        return await self._receive()


class LaissezMcpServerMiddleware:
    def __init__(self, app: StarletteWithLifespan, tools: List[PaidTool], wallet: Account):
        self.app = app
        self.tools = tools
        self.wallet = wallet
        self.facilitator = FacilitatorClient()
        self.settlement_lock = asyncio.Lock()

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        method = scope.get("method", "")
        path = scope.get("path", "")
        scheme = scope.get("scheme", "https")

        # Check if it's an MCP POST request
        if method != "POST" or not path.startswith("/mcp"):
            print(f"[x402] Not an MCP request, passing through")
            await self.app(scope, receive, send)
            return
        
        # Parse the MCP request body
        body = b''
        more_body = True
        while more_body:
            message = await receive()
            if message['type'] == 'http.request':
                body += message.get('body', b'')
                more_body = message.get('more_body', False)
        
        receive_replay = RequestReplay(receive, body)

        # Parse the tool action
        tool_action = None
        if body:
            try:
                mcp_request = json.loads(body)
                tool_action = mcp_request.get("method")
            except json.JSONDecodeError:
                print(f"[x402] Failed to parse MCP request: {body}")

        if tool_action != "tools/call":
            print(f"[x402] Not a tool call, passing through")
            await self.app(scope, receive_replay, send)
            return

        # Parse the tool name
        tool_parameters = mcp_request.get("params", {})
        tool_name = tool_parameters.get("name")

        if not tool_name:
            print(f"[x402] No tool name found, passing through")
            await self.app(scope, receive_replay, send)
            return

        print(f"[x402] Found tool name: {tool_name}")

        # Check if the tool is in the payment config
        tool_names = [tool.name for tool in self.tools]
        if tool_name not in tool_names:
            print(f"[x402] Tool {tool_name} not in payment config, passing through")
            await self.app(scope, receive_replay, send)
            return

        # Build the payment requirements
        headers = { k.decode().lower(): v.decode() for k, v in scope.get("headers", []) }
        tool = self.tools[tool_names.index(tool_name)]
        price = str(tool.price)
        network = tool.network

        try:
            max_amount, asset_address, eip712 = process_price_to_atomic_amount(price, network)
        except ValueError as e:
            error_response = JSONResponse(content={"error": f"Invalid price configuration: {str(e)}"}, status_code=500)
            await error_response(scope, receive_replay, send)
            return

        host = headers.get("host", "")
        resource_url = f"{scheme}://{host}{path}"
        
        payment_requirements = [
            PaymentRequirements(
                scheme="exact",
                network=cast(SupportedNetworks, network),
                asset=asset_address,
                max_amount_required=max_amount,
                resource=resource_url,
                description=tool.description,
                mime_type="application/json",
                pay_to=self.wallet.address,
                max_timeout_seconds=60,
                extra=eip712,
            )
        ]

        # Check if payment is required
        if 'x-payment' not in headers:
            print(f"[x402] Payment required for tool: {tool_name}")

            response_data = x402PaymentRequiredResponse(
                x402_version=x402_VERSION,
                accepts=payment_requirements,
                error=f"Payment required for {tool_name}",
            ).model_dump(by_alias=True)

            error_response = JSONResponse(content=response_data, status_code=402)
            await error_response(scope, receive_replay, send)
            return

        # Decode the X-Payment header
        try:
            payment_dictionary = json.loads(base64.b64decode(headers['x-payment']))
            payment = PaymentPayload(**payment_dictionary)
        except Exception as e:
            print(f"[x402] Failed to decode X-Payment header: {e}")
            error_response = JSONResponse(content={"error": f"Invalid payment header format: {str(e)}"}, status_code=400)
            await error_response(scope, receive_replay, send)
            return
            
        selected_payment_requirements = find_matching_payment_requirements(
            payment_requirements=payment_requirements,
            payment=payment
        )


        if not selected_payment_requirements:
            print(f"[x402] No matching payment requirements found, passing through")
            error_response = JSONResponse(content={"error": f"No matching payment requirements found"}, status_code=400)
            await error_response(scope, receive_replay, send)
            return


        verify_response = await self.facilitator.verify(payment, selected_payment_requirements)

        if not verify_response.is_valid:
            print(f"[x402] Payment verification failed: {verify_response.invalid_reason}")
            error_response = JSONResponse(content={"error": f"Payment verification failed: {verify_response.invalid_reason}"}, status_code=402)
            await error_response(scope, receive_replay, send)
            return


        async def send_wrapper(message: Message):
            if message['type'] == 'http.response.start':
                status_code = message['status']
                if 200 <= status_code < 300:
                    try:
                        settle_response = None
                        async with self.settlement_lock:
                            settle_response = await self.facilitator.settle(payment, selected_payment_requirements)

                        if settle_response and settle_response.success:
                            settlement_header = base64.b64encode(
                                settle_response.model_dump_json(by_alias=True).encode('utf-8')
                            ).decode('utf-8')
                            message['headers'].append(
                                (b'X-Payment-Response', settlement_header.encode('utf-8'))
                            )
                            message['headers'].append(
                                (b'Access-Control-Expose-Headers', b'X-Payment-Response')
                            )
                        else:
                            print(f"[x402] Settlement failed: {settle_response.error_reason if settle_response else 'Unknown reason'}")
                            error_body = json.dumps({"error": "Payment settlement failed"}).encode('utf-8')
                            await send({
                                'type': 'http.response.start',
                                'status': 402,
                                'headers': [
                                    (b'content-type', b'application/json'),
                                    (b'content-length', str(len(error_body)).encode('utf-8'))
                                ]
                            })
                            await send({
                                'type': 'http.response.body',
                                'body': error_body,
                                'more_body': False
                            })
                            return
                    except Exception as e:
                        print(f"[x402] Settlement error: {e}")
                        error_body = json.dumps({"error": "Internal server error during payment settlement"}).encode('utf-8')
                        await send({
                            'type': 'http.response.start',
                            'status': 500,
                            'headers': [
                                (b'content-type', b'application/json'),
                                (b'content-length', str(len(error_body)).encode('utf-8'))
                            ]
                        })
                        await send({
                            'type': 'http.response.body',
                            'body': error_body,
                            'more_body': False
                        })
                        return
            await send(message)

        print(f"[x402] Payment verified, passing to application")
        
        await self.app(scope, receive_replay, send_wrapper)





async def create_paid_mcp_app(mcp: FastMCP, tools: List[PaidTool], wallet: Optional[Account] = None) -> StarletteWithLifespan:

    wallet = check_and_create_wallet(wallet)
    mcp_tools = await mcp.get_tools()
    processed_tools = []
    for tool in tools:
        if tool.name not in mcp_tools:
            print(f"[Laissez] Tool {tool.name} not found in MCP server. Skipping...")
            continue
        else:
            processed_tools.append(tool)
        

    app = mcp.http_app(
        transport='streamable-http',
        stateless_http=True
    )
    app.add_middleware(LaissezMcpServerMiddleware, tools=processed_tools, wallet=wallet)
    return app