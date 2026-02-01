import os
import sys
import time
import joblib
import numpy as np
from datetime import date, datetime

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_operations import insert_transaction

from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

# Load ML Model

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "data", "transaction_model.pkl")
model = joblib.load(MODEL_PATH)

# Plaid setup

configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        "clientId": "696a674e288ea1001d0ff38d",
        "secret": "5b6befbd2fb1f04dbb4ca09c9da7cb"
    }
)

client = plaid_api.PlaidApi(ApiClient(configuration))

ACCESS_TOKEN = "access-sandbox-a1dc8c1c-16ba-48fc-a53f-3d9ddffaea3f"  #  paste from create_access_token.py

# Prediction function

import pandas as pd

def predict_total(quantity, price, txn_time):
    X_live = pd.DataFrame(
        [[quantity, price, txn_time.hour, txn_time.weekday()]],
        columns=["quantity","price","transaction_hour","transaction_dayofweek"]
    )
    return round(float(model.predict(X_live)[0]), 2)

# category 
def auto_category(price):
    amt = abs(price)

    if price < 0 and amt <= 50:
        return 1, "Snacks"
    elif price < 0 and 51 <= amt <= 300:
        return 1, "Lunch"
    elif price < 0 and 301 <= amt <= 1500:
        return 3, "Shopping"
    elif price < 0 and amt > 1500:
        return 4, "Electronics"
    else:
        return None, None   


# Fetch transactions

def fetch_and_store():
    request = TransactionsGetRequest(
        access_token=ACCESS_TOKEN,
        start_date=date(2024, 1, 1),
        end_date=date.today(),
        options=TransactionsGetRequestOptions(count=5)
    )

    response = client.transactions_get(request)

    for txn in response["transactions"]:
        txn_time = datetime.combine(txn["date"], datetime.min.time())
        total = predict_total(1, txn["amount"], txn_time)

        category_id, description = auto_category(txn["amount"])

        insert_transaction(
        user_id=1,
        product_id=1,
        quantity=1,
        price=txn["amount"],
        transaction_time=txn_time,
        category_id=category_id,
        description=description
        )
        print(f"Inserted: {txn['name']} | Predicted Total: {total}")


try:
    while True:
        fetch_and_store()
        time.sleep(60)
except KeyboardInterrupt:
    print("\nStopped by user. Exiting gracefully...")




