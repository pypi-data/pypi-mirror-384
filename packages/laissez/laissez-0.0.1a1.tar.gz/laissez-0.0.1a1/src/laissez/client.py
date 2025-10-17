"""
==========
LAISSEZ
==========
"""


from typing import Callable, Dict, List
from eth_account import Account
from httpx import AsyncClient, Response
from x402.clients.base import MissingRequestConfigError, PaymentError, decode_x_payment_response, x402Client
from x402.clients.httpx import HttpxHooks, x402HttpxClient as BaseX402HttpxClient
from x402.types import x402PaymentRequiredResponse


class LaissezClient(BaseX402HttpxClient):
    def __init__(self, account: Account, **kwargs):
        class LaissezHttpxHooks(HttpxHooks):
            def __init__(self, client: x402Client):
                super().__init__(client=client)

            async def on_response(self, response: Response) -> Response:
                if response.status_code != 402:
                    return response

                if response.request and response.request.extensions.get("x402_retry"):
                    return response

                try:
                    if not response.request:
                        raise MissingRequestConfigError("Missing request configuration")

                    await response.aread()
                    data = response.json()
                    payment_response = x402PaymentRequiredResponse(**data)

                    selected_requirements = self.client.select_payment_requirements(
                        payment_response.accepts
                    )

                    print(f"[Client] Payment required: {selected_requirements.description} for resource {selected_requirements.resource}")

                    payment_header = self.client.create_payment_header(
                        selected_requirements, payment_response.x402_version
                    )

                    request = response.request
                    request.headers["X-Payment"] = payment_header
                    request.headers["Access-Control-Expose-Headers"] = "X-Payment-Response"
                    request.extensions["x402_retry"] = True

                    async with AsyncClient(follow_redirects=True, timeout=30.0) as client:
                        retry_response = await client.send(request)

                    if 200 <= retry_response.status_code < 300:
                        payment_info = "with unknown details"
                        
                        if 'x-payment-response' in retry_response.headers:
                            try:
                                decoded_header = decode_x_payment_response(retry_response.headers['x-payment-response'])
                                payment_info = f"Transaction: {decoded_header.get('transaction')}\n\tPayer: {decoded_header.get('payer')}\n\tNetwork: {decoded_header.get('network')}"
                            except Exception as e:
                                payment_info = f"with settlement details that could not be decoded: {e}"

                        print(f"[Client] Payment successful:\n\t{payment_info}")

                    response.status_code = retry_response.status_code
                    response.headers = retry_response.headers
                    response._content = retry_response.content
                    response.request = retry_response.request
                    
                    return response

                except PaymentError as e:
                    raise e
                except Exception as e:
                    raise PaymentError(f"Failed to handle payment: {str(e)}") from e


        def laissez_hooks(
            account: Account
        ) -> Dict[str, List[Callable]]:
            client = x402Client(account=account)
            hooks = LaissezHttpxHooks(client=client)
            return {
                "request": [hooks.on_request],
                "response": [hooks.on_response],
            }


        super().__init__(account=account, follow_redirects=True, timeout=30.0, **kwargs)
        self.event_hooks = laissez_hooks(account=account)