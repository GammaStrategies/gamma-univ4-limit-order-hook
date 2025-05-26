// SPDX-License-Identifier: BSL
pragma solidity ^0.8.24;

import {BalanceDelta} from "v4-core/types/BalanceDelta.sol";
import {PoolId} from "v4-core/types/PoolId.sol";
import {PoolKey} from "v4-core/types/PoolKey.sol";
import {Currency} from "v4-core/types/Currency.sol";

interface ILimitOrderManager {
    // =========== Structs ===========
    struct PositionTickRange {
        int24 bottomTick;
        int24 topTick;
        bool isToken0;
    }

    struct ClaimableTokens {
        Currency token;  
        uint256 principal;
        uint256 fees;
    }

    struct UserPosition {
        uint128 liquidity;                
        BalanceDelta lastFeePerLiquidity; 
        BalanceDelta claimablePrincipal;  
        BalanceDelta fees;                
    }

    struct PositionState {
        BalanceDelta feePerLiquidity;  
        uint128 totalLiquidity;        
        bool isActive;
        bool isWaitingKeeper;
        uint256 currentNonce;
    }

    struct PositionInfo {
        uint128 liquidity;
        BalanceDelta fees;
        bytes32 positionKey;
    }

    struct PositionBalances {
        uint256 principal0;
        uint256 principal1;
        uint256 fees0;
        uint256 fees1;
    }

    struct CreateOrderResult {
        uint256 usedAmount;
        bool isToken0;
        int24 bottomTick;
        int24 topTick;
    }

    struct ScaleOrderParams {
        bool isToken0;
        int24 bottomTick;
        int24 topTick;
        uint256 totalAmount;
        uint256 totalOrders;
        uint256 sizeSkew;
    }
    struct OrderInfo {
        int24 bottomTick;
        int24 topTick;
        uint256 amount;
        uint128 liquidity;
    }

    struct CreateOrdersCallbackData {
        PoolKey key;
        OrderInfo[] orders;
        bool isToken0;
        address orderCreator;
    }

    struct CancelOrderCallbackData {
        PoolKey key;
        int24 bottomTick;
        int24 topTick;
        uint128 liquidity;
        address user;
        bool isToken0;
    }

    struct ClaimOrderCallbackData {
        BalanceDelta principal;
        BalanceDelta fees;
        PoolKey key;
        address user;
    }

    struct KeeperExecuteCallbackData {
        PoolKey key;
        bytes32[] positions;
    }

    struct UnlockCallbackData {
        CallbackType callbackType;
        bytes data;
    }

    enum CallbackType {
        CREATE_ORDERS,
        // CREATE_ORDER,
        CLAIM_ORDER,
        CANCEL_ORDER,
        // CREATE_SCALE_ORDERS,
        KEEPER_EXECUTE_ORDERS
    }

    // =========== Errors ===========

    error FeePercentageTooHigh();
    error AmountTooLow();
    error AddressZero();
    error NotAuthorized();
    error PositionIsWaitingForKeeper();
    error ZeroLimit();
    error NotWhitelistedPool();
    error MinimumAmountNotMet(uint256 provided, uint256 minimum);
    error MaxOrdersExceeded();
    error UnknownCallbackType();

    // =========== Events ===========
    event OrderClaimed(address owner, PoolId indexed poolId, bytes32 positionKey, uint256 principal0, uint256 principal1, uint256 fees0, uint256 fees1, uint256 hookFeePercentage);
    event OrderCreated(address user, PoolId indexed poolId, bytes32 positionKey);
    event OrderCanceled(address orderOwner, PoolId indexed poolId, bytes32 positionKey);
    event OrderExecuted(PoolId indexed poolId, bytes32 positionKey);
    event PositionsLeftOver(PoolId indexed poolId, bytes32[] leftoverPositions);
    event KeeperWaitingStatusReset(bytes32 positionKey, int24 bottomTick, int24 topTick, int24 currentTick);
    event HookFeePercentageUpdated (uint256 percentage);

    // =========== Functions ===========
    function createLimitOrder(
        bool isToken0,
        int24 targetTick,
        uint256 amount,
        PoolKey calldata key
    ) external payable returns (CreateOrderResult memory);

    function createScaleOrders(
        bool isToken0,
        int24 bottomTick,
        int24 topTick,
        uint256 totalAmount,
        uint256 totalOrders,
        uint256 sizeSkew,
        PoolKey calldata key
    ) external payable returns (CreateOrderResult[] memory results);

    function setHook(address _hook) external;

    function setHookFeePercentage(uint256 _percentage) external;
    
    function executeOrder(
        PoolKey calldata key,
        int24 tickBeforeSwap,
        int24 tickAfterSwap,
        bool zeroForOne
    ) external;

    function cancelOrder(PoolKey calldata key, bytes32 positionKey) external;

    function positionState(PoolId poolId, bytes32 positionKey) 
        external 
        view 
        returns (
            BalanceDelta feePerLiquidity,
            uint128 totalLiquidity,
            bool isActive,
            bool isWaitingKeeper,
            uint256 currentNonce
        );

    function cancelBatchOrders(
        PoolKey calldata key,
        uint256 offset,             
        uint256 limit
    ) external;

    /// @notice Emergency function for keepers to cancel orders on behalf of users
    /// @dev Only callable by keepers to handle emergency situations
    /// @param key The pool key identifying the specific Uniswap V4 pool
    /// @param positionKeys Array of position keys to cancel
    /// @param user The address of the user whose orders to cancel
    function emergencyCancelOrders(
        PoolKey calldata key,
        bytes32[] calldata positionKeys,
        address user
    ) external;

    /// @notice Keeper function to claim positions on behalf of users
    /// @dev Only callable by keepers to help users claim their executed positions
    /// @param key The pool key identifying the specific Uniswap V4 pool
    /// @param positionKeys Array of position keys to claim
    /// @param user The address of the user whose positions to claim
    function keeperClaimPositionKeys(
        PoolKey calldata key,
        bytes32[] calldata positionKeys,
        address user
    ) external;

    function claimOrder(PoolKey calldata key, bytes32 positionKey) external;

    /// @notice Claims multiple positions using direct position keys
    /// @dev This is more robust than using indices as position keys don't shift when other positions are removed
    /// @param key The pool key identifying the specific Uniswap V4 pool
    /// @param positionKeys Array of position keys to claim
    function claimPositionKeys(
        PoolKey calldata key,
        bytes32[] calldata positionKeys
    ) external;

    /// @notice Cancels multiple positions using direct position keys
    /// @dev This is more robust than using indices as position keys don't shift when other positions are removed
    /// @param key The pool key identifying the specific Uniswap V4 pool
    /// @param positionKeys Array of position keys to cancel
    function cancelPositionKeys(
        PoolKey calldata key,
        bytes32[] calldata positionKeys
    ) external;

    /// @notice Batch claims multiple orders that were executed or canceled
    /// @dev Uses pagination to handle large numbers of orders
    /// @param key The pool key identifying the specific Uniswap V4 pool
    /// @param offset Starting position in the user's position array
    /// @param limit Maximum number of positions to process in this call
    function claimBatchOrders(
        PoolKey calldata key,
        uint256 offset,             
        uint256 limit
    ) external;

    function executeOrderByKeeper(PoolKey calldata key, bytes32[] memory waitingPositions) external;
    function setKeeper(address _keeper, bool _isKeeper) external;
    function setExecutablePositionsLimit(uint256 _limit) external;
    function setMinAmount(Currency currency, uint256 _minAmount) external;

    // View functions
    function getUserPositions(address user, PoolId poolId, uint256 offset, uint256 limit) external view returns (PositionInfo[] memory positions);



    // Additional view functions for state variables
    function currentNonce(PoolId poolId, bytes32 baseKey) external view returns (uint256);
    function treasury() external view returns (address);
    function executablePositionsLimit() external view returns (uint256);
    function isKeeper(address) external view returns (bool);
    function minAmount(Currency currency) external view returns (uint256);

    function getUserPositionCount(address user, PoolId poolId) external view returns (uint256);
}