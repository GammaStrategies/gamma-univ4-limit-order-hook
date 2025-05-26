# LimitOrderHook System

A comprehensive limit order system for Uniswap v4 pools, enabling single-price limit orders and scale orders with keeper functionality and fee management.

## License

This project is licensed under the Business Source License 1.1 (BSL 1.1) - see the LICENSE file for details. The BSL is a limited commercial license that converts to an open source license after a specified period. 

## Overview

The LimitOrderHook system consists of three main components:
- LimitOrderHook: Core hook contract handling swap events
- LimitOrderManager: Advanced order management and execution logic
- Supporting Libraries: Specialized functionality for position management, callbacks, and tick calculations

## Key Features

### Order Types
- Single-tick limit orders
- Scale orders (multiple limit orders across a price range)

### Order Management
- Batch order creation and cancellation
- Position tracking and fee accounting
- Keeper system for handling excess orders
- Minimum order amount enforcement

### Fee Distribution
- Per-position fee tracking
- Multi-user fee sharing for shared positions
- Automated fee settlement during claims

## Architecture

### LimitOrderHook
Primary hook contract interfacing with Uniswap v4 pools.

```solidity
contract LimitOrderHook is BaseHook {
    LimitOrderManager public immutable limitOrderManager;
    
    // Hooks implemented:
    - beforeSwap: Records tick before swap
    - afterSwap: Triggers order execution
}
```

### LimitOrderManager
Core order management contract handling:
- Order creation and cancellation
- Position tracking
- Fee management
- Keeper operations

```solidity
contract LimitOrderManager is ILimitOrderManager, IUnlockCallback, Ownable, ReentrancyGuard, Pausable {
    // Key state variables
    mapping(PoolId => mapping(bytes32 => PositionState)) public positionState;
    mapping(PoolId => mapping(bytes32 => mapping(address => UserPosition))) public userPositions;
    mapping(address => mapping(PoolId => EnumerableSet.Bytes32Set)) private userPositionKeys;
    mapping(PoolId => mapping(bytes32 => uint256)) public currentNonce;
    
    // Core functionality
    function createLimitOrder(...) external payable returns (CreateOrderResult memory)
    function createScaleOrders(...) external payable returns (CreateOrderResult[] memory)
    function executeOrder(...) external
    function cancelOrder(...) external
    function claimOrder(...) external
    function cancelPositionKeys(...) external
    function claimPositionKeys(...) external
    function getUserPositionCount(...) external view returns (uint256)
}
```

## Key Concepts

### Order Creation Process
1. Validate input parameters and amounts
2. Calculate tick ranges based on order type
3. Handle token transfers
4. Create liquidity position
5. Update position tracking
6. Emit relevant events

### Execution Flow
1. Swap triggers hook callback
2. Find overlapping positions
3. Execute positions within limit
4. Mark excess positions for keeper
5. Update position states
6. Distribute fees

### Fee Management
- Fees tracked per position using feePerLiquidity accumulator
- User fees distributed proportionally to liquidity contribution

## Usage Examples

### Creating a Single Limit Order
```solidity
CreateOrderResult memory result = limitOrderManager.createLimitOrder(
    true,           // isToken0
    targetTick,     // price tick
    1 ether,        // amount
    poolKey         // pool identification
);
```

### Creating Scale Orders
```solidity
CreateOrderResult[] memory results = limitOrderManager.createScaleOrders(
    true,           // isToken0
    bottomTick,     // range start
    topTick,        // range end
    10 ether,       // total amount
    5,              // number of orders
    1.5e18,         // size skew
    poolKey
);
```

### Keeper Operations
```solidity
// Execute leftover positions
limitOrderManager.executeOrderByKeeper(
    poolKey,
    waitingPositions  // positions marked for keeper execution
);
```

## Security Considerations

### Access Control
- Owner-only functions for configuration
- Keeper validation for specialized operations
- Position-based access control for user operations

### Safety Checks
- Minimum amount validation
- Tick range validation
- Position state verification
- Duplicate execution prevention

### Fee Protection
- Safe fee calculation and distribution
- Multi-user fee tracking

## Gas Optimization Features

- Batch operations for order management
- Efficient position tracking using EnumerableSet
- Optimized fee calculations
- Smart keeper system to handle high load

## Configuration Options

### Owner Controls
- Set executable positions limit
- Configure minimum order amounts
- Manage keeper addresses

### System Limits
- Maximum orders per pool
- Executable positions per transaction
- Minimum order amounts per token

## Events

```solidity
event OrderCreated(address user, PoolId indexed poolId, bytes32 positionKey);
event OrderCanceled(address orderOwner, PoolId indexed poolId, bytes32 positionKey);
event OrderExecuted(PoolId indexed poolId, bytes32 positionKey);
event PositionsLeftOver(PoolId indexed poolId, bytes32[] leftoverPositions);
```

## Development and Testing

The system includes comprehensive test suites covering:
- Basic order operations
- Scale order functionality
- Keeper system
- Fee distribution
- Gas optimization
- Edge cases and security scenarios

## Dependencies

- Uniswap v4 core contracts
- OpenZeppelin contracts
- Safe math libraries
- Custom position management libraries