"""
==========
LAISSEZ
==========
"""


from typing import Callable, Dict, List, Optional
from eth_account import Account
from httpx import AsyncClient, Response
from pydantic import BaseModel
from x402.clients.base import MissingRequestConfigError, PaymentError, decode_x_payment_response, x402Client
from x402.clients.httpx import HttpxHooks, x402HttpxClient as BaseX402HttpxClient
from x402.types import x402PaymentRequiredResponse
import os
import csv
from datetime import datetime, timezone
from laissez.common import check_and_create_wallet


class PaymentLog(BaseModel):
    transaction_hash: str
    network: str
    description: str
    paid_to: str
    paid_by: str
    amount: str
    unit: str




class LaissezClient(BaseX402HttpxClient):
    def __init__(self, wallet: Optional[Account] = None, **kwargs):

        wallet = check_and_create_wallet(wallet)

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
                        decoded_header = {}
                        
                        if 'x-payment-response' in retry_response.headers:
                            try:
                                decoded_header = decode_x_payment_response(retry_response.headers['x-payment-response'])
                                payment_info = f"Transaction: {decoded_header.get('transaction')}\n\tPayer: {decoded_header.get('payer')}\n\tNetwork: {decoded_header.get('network')}"
                            except Exception as e:
                                payment_info = f"with settlement details that could not be decoded: {e}"

                        print(f"[Client] Payment successful:\n\t{payment_info}")

                        # post to laissez db
                        payment_log = PaymentLog(
                            transaction_hash=decoded_header.get("transaction", "unknown"),
                            network=selected_requirements.network,
                            description=selected_requirements.description,
                            paid_to=selected_requirements.pay_to,
                            paid_by=decoded_header.get("payer", self.client.account.address),
                            amount=selected_requirements.max_amount_required,
                            unit=selected_requirements.extra.get("name", "unknown"),
                        )

                        # Ensure directory exists
                        cwd = os.getcwd()
                        laissez_dir = os.path.join(cwd, ".laissez")
                        filepath = os.path.join(laissez_dir, "payments.csv")
                        os.makedirs(laissez_dir, exist_ok=True)

                        write_header = not os.path.exists(filepath)

                        # Prepare the row
                        row = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "transaction_hash": payment_log.transaction_hash,
                            "network": payment_log.network,
                            "description": payment_log.description,
                            "paid_to": payment_log.paid_to,
                            "paid_by": payment_log.paid_by,
                            "amount": payment_log.amount,
                            "unit": payment_log.unit,
                        }

                        # Write to CSV
                        with open(filepath, mode="a", newline="", encoding="utf-8") as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=list(row.keys()))
                            if write_header:
                                writer.writeheader()
                            writer.writerow(row)

                        response.status_code = retry_response.status_code
                        response.headers = retry_response.headers
                        response._content = retry_response.content
                        response.request = retry_response.request
                    
                        return response
                    else:
                        await retry_response.aread()
                        message = f"Payment failed with status code {retry_response.status_code}"
                        try:
                            data = retry_response.json()
                            if "error" in data:
                                message += f": {data['error']}"
                        except Exception:
                            message += f". Body: {retry_response.text}"
                        raise PaymentError(message)

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


        super().__init__(account=wallet, follow_redirects=True, timeout=30.0, **kwargs)
        self.event_hooks = laissez_hooks(account=wallet)