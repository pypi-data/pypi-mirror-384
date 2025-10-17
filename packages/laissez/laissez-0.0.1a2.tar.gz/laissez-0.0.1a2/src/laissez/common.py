import os
import secrets
from eth_account import Account
from typing import Optional


def check_and_create_wallet(wallet: Optional[Account] = None) -> Account:
    if wallet is None:
        wallet_pk = os.getenv("WALLET_PRIVATE_KEY")
        if wallet_pk:
            wallet = Account.from_key(wallet_pk)
            print(f"[Laissez] Loaded wallet from .env file")
            print(f"[Laissez] Wallet address: {wallet.address}")
        else:
            wallet_creation_prompt = """
No wallet found. 
If you have a wallet private key, please set WALLET_PRIVATE_KEY in the .env file and run the server again.
If you don't have a wallet private key, you can create one now.
Note: If you choose to create a wallet, Laissez will add the wallet private key to the .env file.

Would you like to create a wallet now? (Y/n) >>> """
            wallet_creation_response = input(wallet_creation_prompt)
            if wallet_creation_response.lower() == "y" or wallet_creation_response.lower() == "":
                random_string = secrets.token_urlsafe(32)
                wallet = Account.create(random_string)
                env_file = ".env"
                with open(env_file, "a", encoding="utf-8") as f:
                    f.write(f"\nWALLET_PRIVATE_KEY={wallet.key.hex()}\n")
                    print("[Laissez] Wallet created and saved to .env file")

                print("="*50)
                print(f"[Laissez] SAVE THIS FOR FUTURE USE")
                print(f"[Laissez] Wallet address: {wallet.address}")
                print(f"[Laissez] Wallet private key: {wallet.key.hex()}")
                print("="*50)
            else:
                raise ValueError("No wallet found and user did not want to create one")
    return wallet