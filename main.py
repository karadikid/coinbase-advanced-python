import os
from dotenv import load_dotenv
from coinbaseadvanced.client import CoinbaseAdvancedTradeAPIClient

load_dotenv()


# Creating the client.
client = CoinbaseAdvancedTradeAPIClient(api_key=os.getenv('API_KEY'), secret_key=os.getenv('SECRET_KEY'))

# Listing accounts.
accounts_page = client.list_accounts(100)
# print(accounts_page.size)
#for x in range(len(self.accounts_page.size)):
 #   print self.accounts_page.size[x]
for account in accounts_page:
    print(account.name)

# List products
products_page = client.list_products()
# print(products_page)

for item in products_page.products:
    print(item.product_id)


# Creating a limit order.
# order_created = client.create_limit_order(client_order_id="lknalksdj89asdkl", product_id="ALGO-USD", side=Side.BUY, limit_price=".19", base_size=5)
