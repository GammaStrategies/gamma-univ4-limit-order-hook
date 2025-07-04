#pip install gamma-books
from gamma_books import client
import json
import os

#load config
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Config file not found at {config_path}")
    print("Please copy config.json.example to config.json and update with your values")
    exit(1)

#connect wallet
network_name = 'base'  #base/unichain/arbitrum
wallet_key = config['wallet_key']  #your wallet private key
me=client(network_name,wallet_key)

#get pools
pools=me.get_pools()
print(pools)

#get book
pool_id='0xc58b1cb202c4650f52cbc51193783cb0c245419028bfe1bb00b786a9e0187372'
invert=False #to invert pool's base token and quote token
window=0.1 #applied to pool price to set the portion of the book to get
book=me.get_book(pool_id,invert,window)
print(book)

#plot book
cumulative=False
me.plot_book(book,cumulative)

#place limit order
pool_id='0xc58b1cb202c4650f52cbc51193783cb0c245419028bfe1bb00b786a9e0187372'
invert=False #to invert pool's base token and quote token
side='buy' #buy/sell
range=me.get_extreme_prices(pool_id,invert,side) #get order's valid price range
print(range)
size=15 #order's size in provided token
price=2000 #order's execution price
receipt=me.place_limit_order(pool_id,invert,side,size,price)

#place limit orders
pool_id='0xc58b1cb202c4650f52cbc51193783cb0c245419028bfe1bb00b786a9e0187372'
invert=False #to invert pool's base token and quote token
side='buy' #buy/sell
range=me.get_extreme_prices(pool_id,invert,side) #get orders' valid price range
print(range)
size=20 #orders' total size in provided token
lower_price=2484.959 #lower order's execution price
upper_price=2497.415 #upper order's execution price
range=me.get_extreme_counts(pool_id,lower_price,upper_price) #get orders' valid count range
print(range)
count=6 #number of orders
skew=2 #size ratio between upper order and lower order
receipt=me.place_limit_orders(pool_id,invert,side,size,lower_price,upper_price,count,skew)

#place market order
pool_id='0xc58b1cb202c4650f52cbc51193783cb0c245419028bfe1bb00b786a9e0187372'
invert=False #to invert pool's base token and quote token
side='buy' #buy/sell
size=10 #orders' total size in provided token
slippage=0.01 #order's maximum allowed slippage
receipt=me.place_market_order(pool_id,invert,side,size,slippage)

#get orders
orders=me.get_orders()
print(orders)

#cancel order
pool_id=orders[0]['pool_id']
order_id=orders[0]['order_id']
receipt=me.cancel_order(pool_id,order_id)

#claim order
pool_id=orders[0]['pool_id']
order_id=orders[0]['order_id']
receipt=me.claim_order(pool_id,order_id)

#cancel orders
pool_id=orders[0]['pool_id']
receipt=me.cancel_orders(pool_id)

#claim orders
pool_id=orders[0]['pool_id']
receipt=me.claim_orders(pool_id)