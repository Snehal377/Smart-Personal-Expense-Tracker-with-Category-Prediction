from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products

configuration = Configuration(
    host="https://sandbox.plaid.com",
    api_key={
        "clientId": "696a674e288ea1001d0ff38d",
        "secret": "5b6befbd2fb1f04dbb4ca09c9da7cb"
    }
)

client = plaid_api.PlaidApi(ApiClient(configuration))

# Create public token
sandbox_response = client.sandbox_public_token_create(
    SandboxPublicTokenCreateRequest(
        institution_id="ins_109508",
        initial_products=[Products("transactions")]
    )
)

public_token = sandbox_response["public_token"]

# Exchange to access token
exchange_response = client.item_public_token_exchange(
    ItemPublicTokenExchangeRequest(public_token=public_token)
)

access_token = exchange_response["access_token"]

print("SAVE THIS ACCESS TOKEN:")
print(access_token)
