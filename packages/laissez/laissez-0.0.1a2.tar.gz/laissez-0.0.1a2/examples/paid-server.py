from fastapi import FastAPI
from x402.fastapi.middleware import require_payment
import random

app = FastAPI()

app.middleware("http")(
    require_payment(
        path="/roll-dice",
        price="$0.001",
        pay_to_address="0x58635e118B55F67f75B4dFD44f3cd612eC536e0a",
        network="base-sepolia",
        description="Roll a dice"
    )
)

app.middleware("http")(
    require_payment(
        path="/multiply",
        price="$0.005",
        pay_to_address="0x58635e118B55F67f75B4dFD44f3cd612eC536e0a",
        network="base-sepolia",
        description="Multiply two numbers"
    )
)

@app.get("/roll-dice")
def roll_dice():
    dice_roll = random.randint(1, 6)
    return { "dice_roll": dice_roll } 


@app.get("/multiply")
def multiply(a: int, b: int):
    return { "result": a * b }