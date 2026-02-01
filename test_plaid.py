 # connect api and fetch live data. and test plaid and also insert transaction into MYSQL. 

from plaid.api import plaid_api #Main class to call Plaid APIs
from plaid.configuration import Configuration #Plaid environment setup sandbox
from plaid.api_client import ApiClient  #Handles API requests
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest #sandbox to create a fake bank login token
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest#REQUIRED to fetch transactions.
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from datetime import date ,datetime
from plaid.model.products import Products #tells Plaid you want transaction data
from plaid.model.sandbox_item_fire_webhook_request import SandboxItemFireWebhookRequest 

from plaid.model.webhook_type import WebhookType #Used for webhooks testing (real-time updates)
import time
from db_operations import insert_transaction


configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        "clientId": "696a674e288ea1001d0ff38d",
        "secret": "5b6befbd2fb1f04dbb4ca09c9da7cb"
    }
)

api_client = ApiClient(configuration)  #handles HTTP requests
client = plaid_api.PlaidApi(api_client)  #object used to call Plaid APIs

# to create sandbox public token 
sandbox_request = SandboxPublicTokenCreateRequest(   
    institution_id="ins_109508",  #sandbox fake bank 
    initial_products=[Products("transactions")]  #You request transaction access only

)
#Plaid returns a temporary public token
sandbox_response = client.sandbox_public_token_create(sandbox_request)
public_token = sandbox_response["public_token"]

#Exchange Public Token → Access Token
exchange_request = ItemPublicTokenExchangeRequest(
    public_token=public_token
)

exchange_response = client.item_public_token_exchange(exchange_request)
access_token = exchange_response["access_token"]

#For testing/debugging
print("ACCESS TOKEN:", access_token) # permanent key for transactions


from datetime import date
import time

# Wait a moment for sandbox to prepare data
time.sleep(2)

#Create Transaction Fetch Request
txn_request = TransactionsGetRequest(
    access_token=access_token,
    start_date=date(2024, 1, 1), #fetch transaction between date 
    end_date=date.today(),
    options=TransactionsGetRequestOptions(count=10) #Limit results to 10 transactions
)

try:
    txn_response = client.transactions_get(txn_request) #call plaid API to fetch transaction.
    for txn in txn_response["transactions"]:
        print(txn["name"], txn["amount"], txn["date"])

        # Insert transaction into MySQL
        insert_transaction(
            user_id=txn["account_id"], #Store bank account ID as user reference
            product_id=txn["category_id"][0] if txn.get("category_id") else 0, # store cat is missing store 0 
            quantity=1,  # by default 1 
            price=txn["amount"]  #This is LIVE API and  MySQL pipeline
        )

except Exception as e:
    print("Retrying transaction fetch...")
    time.sleep(2)
    txn_response = client.transactions_get(txn_request)
    for txn in txn_response["transactions"]:
        print(txn["name"], txn["amount"], txn["date"])
