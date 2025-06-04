# Gamma Books - Python SDK

Python SDK for Gamma's Uniswap v4 limit order book smart contract. This SDK allows you to interact with limit order functionality on Base, Unichain, Arbitrum, and other networks that may be added in the future.

## 1. Installation

Install the package using pip:

```bash
pip install gamma-books
```

## Getting Started

First, import the client and initialize it with your network and wallet:

```python
from gamma_books import client

# Initialize client
network_name = 'base'  # 'base' or 'unichain'
wallet_key = 'your_private_key_here'  # Your wallet private key
me = client(network_name, wallet_key)
```

## 2. Get Book & Plot Book

### Getting Pool Information

```python
# Get all available pools
pools = me.get_pools()
print(pools)
```

### Getting Order Book Data

```python
# Get order book for a specific pool
pool_id = '0xc58b1cb202c4650f52cbc51193783cb0c245419028bfe1bb00b786a9e0187372'
invert = False  # Set to True to invert pool's base token and quote token. By default, token0 is base token and token1 is quote token. Determination of token0-token1 ordering is based on alphanumeric order of the token addresses
window = 0.1    # Applied to pool price to set the portion of the book to get (0.1 = 10%)

book = me.get_book(pool_id, invert, window)
print(book)
```

The book object contains:
- `price`: Current pool price
- `bids`: Array of bid orders with price and quantity
- `asks`: Array of ask orders with price and quantity

### Plotting the Order Book

```python
# Plot the order book
cumulative = True  # Set to False for non-cumulative view
me.plot_book(book, cumulative)
```

This will display a matplotlib chart showing:
- Green area: Bid orders
- Red area: Ask orders  
- Black dotted line: Current pool price

## 3. Placing Orders

### Limit Orders (Single Orders)

```python
# Get valid price range for orders
pool_id = '0xc58b1cb202c4650f52cbc51193783cb0c245419028bfe1bb00b786a9e0187372'
invert = False  # To invert pool's base token and quote token. By default, token0 is base token and token1 is quote token. Determination of token0-token1 ordering is based on alphanumeric order of the token addresses
side = 'buy'    # 'buy' or 'sell'

# Get the valid price range for this order type
price_range = me.get_extreme_prices(pool_id, invert, side)
print(f"Valid price range: {price_range}")

# Place a single limit order
size = 20    # Order size in the provided token
price = 2000 # Order execution price

receipt = me.place_order(pool_id, invert, side, size, price)
print(f"Transaction hash: {receipt['transactionHash'].hex()}")
```

### Scale Orders (Multiple Orders)

Scale orders allow you to place multiple orders across a price range with customizable distribution.

```python
# Parameters for scale orders
pool_id = '0xc58b1cb202c4650f52cbc51193783cb0c245419028bfe1bb00b786a9e0187372'
invert = False     # To invert pool's base token and quote token. By default, token0 is base token and token1 is quote token. Determination of token0-token1 ordering is based on alphanumeric order of the token addresses
side = 'buy'       # 'buy' or 'sell'
size = 20          # Total size across all orders
lower_price = 1000 # Lower bound of price range
upper_price = 2000 # Upper bound of price range
count = 10         # Number of orders to create
skew = 2           # Size ratio between upper order and lower order

# Get valid count range for the price range
count_range = me.get_extreme_counts(pool_id, lower_price, upper_price)
print(f"Valid order count range: {count_range}")

# Place scale orders
receipt = me.place_orders(pool_id, invert, side, size, lower_price, upper_price, count, skew)
print(f"Transaction hash: {receipt['transactionHash'].hex()}")
```

**Scale Order Parameters:**
- `size`: Total amount to be distributed across all orders
- `lower_price` / `upper_price`: Price range boundaries
- `count`: Number of individual orders to create
- `skew`: Controls size distribution (higher values put more size at higher prices)

## 4. Getting Orders

```python
# Get all your current orders
orders = me.get_orders()
print(orders)

# Each order contains:
for order in orders:
    print(f"Pool ID: {order['pool_id']}")
    print(f"Order ID: {order['order_id']}")
    print(f"Side: {order['side']}")
    print(f"Size: {order['size']}")
    print(f"Price Range: {order['lower_price']} - {order['upper_price']}")
    print(f"Filled: {order['filled']}")
    print(f"Principal (Base/Quote): {order['principal_base_token']}/{order['principal_quote_token']}")
    print(f"Fees (Base/Quote): {order['fees_base_token']}/{order['fees_quote_token']}")
    print("---")
```

## 5. Canceling Orders

### Cancel Single Order

```python
# Get your orders first
orders = me.get_orders()

if orders:
    # Cancel a specific order
    pool_id = orders[0]['pool_id']
    order_id = orders[0]['order_id']
    
    receipt = me.cancel_order(pool_id, order_id)
    print(f"Cancelled order. Transaction hash: {receipt['transactionHash'].hex()}")
```

### Cancel All Orders in a Pool

```python
# Cancel all orders in a specific pool
pool_id = orders[0]['pool_id']  # Use pool_id from your orders

receipt = me.cancel_orders(pool_id)
print(f"Cancelled all orders in pool. Transaction hash: {receipt['transactionHash'].hex()}")
```

## 6. Claiming Orders

### Claim Single Order

```python
# Get your orders first
orders = me.get_orders()

if orders:
    # Claim rewards from a specific order
    pool_id = orders[0]['pool_id']
    order_id = orders[0]['order_id']
    
    receipt = me.claim_order(pool_id, order_id)
    print(f"Claimed order. Transaction hash: {receipt['transactionHash'].hex()}")
```

### Claim All Orders in a Pool

```python
# Claim all orders in a specific pool
pool_id = orders[0]['pool_id']  # Use pool_id from your orders

receipt = me.claim_orders(pool_id)
print(f"Claimed all orders in pool. Transaction hash: {receipt['transactionHash'].hex()}")
```

## Complete Example

Here's a complete workflow example:

```python
from gamma_books import client

# Initialize
network_name = 'base'
wallet_key = 'your_private_key_here'
me = client(network_name, wallet_key)

# 1. Get available pools
pools = me.get_pools()
print("Available pools:", len(pools))

# 2. Get and plot order book
pool_id = pools[0]['pool_id']  # Use first available pool
book = me.get_book(pool_id, False, 0.1)
me.plot_book(book, True)

# 3. Place a limit order
side = 'buy'
price_range = me.get_extreme_prices(pool_id, False, side)
price = price_range[0] * 1.1  # 10% above minimum
size = 10

receipt = me.place_order(pool_id, False, side, size, price)
print("Order placed!")

# 4. Check your orders
orders = me.get_orders()
print(f"You have {len(orders)} active orders")

# 5. Cancel and claim as needed
if orders:
    # Cancel first order
    me.cancel_order(orders[0]['pool_id'], orders[0]['order_id'])
    
    # Or cancel all orders in the pool
    # me.cancel_orders(orders[0]['pool_id'])
```

## Supported Networks

- **Base**: Ethereum Layer 2 network
- **Unichain**: Uniswap's Layer 2 network
- **Arbitrum**: Ethereum Layer 2 scaling solution

To use any of these networks, simply specify the network name when initializing the client:

```python
# For Base
me = client('base', wallet_key)

# For Unichain  
me = client('unichain', wallet_key)

# For Arbitrum
me = client('arbitrum', wallet_key)
```

## Error Handling

The SDK will raise exceptions for common errors like:
- Invalid pool IDs
- Insufficient balances
- Invalid price ranges
- Network connectivity issues

Always wrap your calls in try-catch blocks for production use:

```python
try:
    receipt = me.place_order(pool_id, False, 'buy', 10, 2000)
    print("Order placed successfully!")
except Exception as e:
    print(f"Error placing order: {e}")
```
