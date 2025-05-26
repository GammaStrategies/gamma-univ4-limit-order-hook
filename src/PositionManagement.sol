// SPDX-License-Identifier: BSL
pragma solidity ^0.8.24;

import {IPoolManager} from "v4-core/interfaces/IPoolManager.sol";
import {PoolId} from "v4-core/types/PoolId.sol";
import {BalanceDelta} from "v4-core/types/BalanceDelta.sol";
import {EnumerableSet} from "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import {ILimitOrderManager} from "./ILimitOrderManager.sol";
import {StateLibrary} from "v4-core/libraries/StateLibrary.sol";
import {FullMath} from "v4-core/libraries/FullMath.sol";
import {TickMath} from "v4-core/libraries/TickMath.sol";
import {BalanceDeltaLibrary} from "v4-core/types/BalanceDelta.sol";
import {LiquidityAmounts} from "@uniswap/v4-core/test/utils/LiquidityAmounts.sol";
import {BalanceDelta, toBalanceDelta} from "v4-core/types/BalanceDelta.sol";
import {PoolKey} from "v4-core/types/PoolKey.sol";
import {TickBitmap} from "v4-core/libraries/TickBitmap.sol";
import {BitMath} from "v4-core/libraries/BitMath.sol";
import "forge-std/console.sol";


library PositionManagement {
    using EnumerableSet for EnumerableSet.AddressSet;
    using EnumerableSet for EnumerableSet.Bytes32Set;
    using BalanceDeltaLibrary for BalanceDelta;

    uint256 internal constant Q128 = 1 << 128;

    // ==== Errors ====
    error InvalidSizeSkew();
    error MinimumAmountNotMet(uint256 provided, uint256 minimum);
    error MaxOrdersExceeded();
    error InvalidTickRange();
    error MinimumTwoOrders();
    error InvalidScaleParameters();
    
    /// @notice Calculates distribution of amounts and corresponding liquidity across scale orders
    /// @param orders Array of OrderInfo structs with tick ranges defined
    /// @param isToken0 True if orders are for token0, false for token1
    /// @param totalAmount Total amount of tokens to distribute across orders
    /// @param totalOrders Number of orders to create
    /// @param sizeSkew Factor determining the distribution of amounts (scaled by 1e18)
    /// @return ILimitOrderManager.OrderInfo[] Updated orders array with amounts and liquidity calculated
    function calculateOrderSizes(
        ILimitOrderManager.OrderInfo[] memory orders,
        bool isToken0,
        uint256 totalAmount,
        uint256 totalOrders,
        uint256 sizeSkew
    ) public pure returns (ILimitOrderManager.OrderInfo[] memory) {
        uint256 totalAmountUsed;
        
        for (uint256 i = 0; i < totalOrders; i++) {
            uint256 orderAmount;
            if (i == totalOrders - 1) {
                orderAmount = totalAmount - totalAmountUsed;
            } else {
                orderAmount = _calculateOrderSize(
                    totalAmount,
                    totalOrders,
                    sizeSkew,
                    i + 1
                );
                totalAmountUsed += orderAmount;
            }
            orders[i].amount = orderAmount;

            // Calculate liquidity
            uint160 sqrtPriceAX96 = TickMath.getSqrtPriceAtTick(orders[i].bottomTick);
            uint160 sqrtPriceBX96 = TickMath.getSqrtPriceAtTick(orders[i].topTick);
            
            orders[i].liquidity = isToken0 
                ? LiquidityAmounts.getLiquidityForAmount0(sqrtPriceAX96, sqrtPriceBX96, orderAmount)
                : LiquidityAmounts.getLiquidityForAmount1(sqrtPriceAX96, sqrtPriceBX96, orderAmount);
        }

        return orders;
    }


    /// @notice Validates the sizes of scale orders against minimum and maximum constraints
    /// @param orders Array of scale orders to validate
    /// @param totalAmount Total amount allocated for all orders
    /// @param minRequired Minimum amount required for each order
    function validateScaleOrderSizes(
        ILimitOrderManager.OrderInfo[] memory orders,
        uint256 totalAmount,
        uint256 minRequired
    ) public pure returns (bool) {
        // if (orders.length == 0) return false;
        
        // Check first and last order sizes
        if (orders[0].amount < minRequired) {
            revert MinimumAmountNotMet(orders[0].amount, minRequired);
        }
        if (orders[orders.length - 1].amount < minRequired) {
            revert MinimumAmountNotMet(orders[orders.length - 1].amount, minRequired);
        }
        
        // Verify total amount bounds
        return orders[0].amount <= totalAmount && 
               orders[orders.length - 1].amount <= totalAmount;
    }

    /// @notice Internal function to calculate the size of a specific order in a scale order series
    /// @param totalSize Total amount of tokens to distribute
    /// @param numOrders Number of orders in the series
    /// @param sizeSkew Skew factor (scaled by 1e18, where 1e18 = no skew)
    /// @param orderIndex Position of order in series (1-based index)
    /// @return uint256 Calculated size for the specified order
    function _calculateOrderSize(
        uint256 totalSize,
        uint256 numOrders,
        uint256 sizeSkew,  // scaled by 1e18
        uint256 orderIndex // 1-based index
    ) public pure returns (uint256) {
        if (orderIndex == 0 || orderIndex > numOrders) revert InvalidScaleParameters();
        

        uint256 numerator1 = 2 * totalSize;
        uint256 denominator1 = numOrders * (1e18 + sizeSkew);
        uint256 basePart = FullMath.mulDiv(numerator1, 1e18, denominator1);
        
        

        uint256 kMinusOne = sizeSkew >= 1e18 ? sizeSkew - 1e18 : 1e18 - sizeSkew;
        uint256 indexRatio = FullMath.mulDiv(orderIndex - 1, 1e18, numOrders - 1);
        uint256 skewComponent = FullMath.mulDiv(kMinusOne, indexRatio, 1e18);
        uint256 multiplier = sizeSkew >= 1e18 ? 
            1e18 + skewComponent : 
            1e18 - skewComponent;
        return FullMath.mulDiv(basePart, multiplier, 1e18);
    }


    struct PositionParams {
        ILimitOrderManager.UserPosition position;
        ILimitOrderManager.PositionState posState;
        IPoolManager poolManager;
        PoolId poolId;
        int24 bottomTick;
        int24 topTick;
        bool isToken0;
        uint256 feeDenom;
        uint256 hookFeePercentage;
    }

    /// @notice Calculates the token balances and fees for a limit order position
    /// @param params See PositionParams above
    /// @return balances 
    function getPositionBalances(
        PositionParams memory params
    ) public view returns (ILimitOrderManager.PositionBalances memory balances) {
        uint160 sqrtPriceAX96 = TickMath.getSqrtPriceAtTick(params.bottomTick);
        uint160 sqrtPriceBX96 = TickMath.getSqrtPriceAtTick(params.topTick);

        // Calculate principals
        if (!params.posState.isActive) {
            if (params.isToken0) {
                balances.principal1 = LiquidityAmounts.getAmount1ForLiquidity(sqrtPriceAX96, sqrtPriceBX96, params.position.liquidity );
            } else {
                balances.principal0 = LiquidityAmounts.getAmount0ForLiquidity( sqrtPriceAX96,sqrtPriceBX96, params.position.liquidity );
            }
        } else {
            (uint160 sqrtPriceX96, , , ) = StateLibrary.getSlot0(params.poolManager, params.poolId);
            (balances.principal0, balances.principal1) = LiquidityAmounts.getAmountsForLiquidity( sqrtPriceX96, sqrtPriceAX96, sqrtPriceBX96, params.position.liquidity );
        }

        BalanceDelta fees;        
        if(params.posState.isActive) {
            (uint256 fee0Global, uint256 fee1Global) = calculatePositionFee(params.poolId, params.bottomTick, params.topTick, params.poolManager);
            fees = getUserProportionateFees(params.position, params.posState, fee0Global, fee1Global);
        } else {

            fees = params.position.fees;
            if (params.position.liquidity != 0) {
                BalanceDelta feeDiff = params.posState.feePerLiquidity - params.position.lastFeePerLiquidity;
                int128 liq = int128(params.position.liquidity);
                fees = params.position.fees + toBalanceDelta(
                    feeDiff.amount0() >= 0 
                        ? int128(int256(FullMath.mulDiv(uint256(uint128(feeDiff.amount0())), uint256(uint128(liq)), 1e18)))
                        : -int128(int256(FullMath.mulDiv(uint256(uint128(-feeDiff.amount0())), uint256(uint128(liq)), 1e18))),
                    feeDiff.amount1() >= 0 
                        ? int128(int256(FullMath.mulDiv(uint256(uint128(feeDiff.amount1())), uint256(uint128(liq)), 1e18)))
                        : -int128(int256(FullMath.mulDiv(uint256(uint128(-feeDiff.amount1())), uint256(uint128(liq)), 1e18)))
                );
            }
        }

        int128 fees0 = fees.amount0();
        int128 fees1 = fees.amount1();
        
        if(fees0 > 0) {
            balances.fees0 = (uint256(uint128(fees0)) * (params.feeDenom - params.hookFeePercentage)) / params.feeDenom;
        }
        if(fees1 > 0) {
            balances.fees1 = (uint256(uint128(fees1)) * (params.feeDenom - params.hookFeePercentage)) / params.feeDenom;
        }
    }

    /// @notice Calculates a user's proportionate share of accumulated fees
    /// @param position User's position data
    /// @param posState Position state
    /// @param globalFees0 Global fees for token0
    /// @param globalFees1 Global fees for token1
    /// @return BalanceDelta User's proportionate share of accumulated fees
    function getUserProportionateFees(
        ILimitOrderManager.UserPosition memory position,
        ILimitOrderManager.PositionState memory posState,
        uint256 globalFees0,
        uint256 globalFees1
    ) public pure returns (BalanceDelta) {
        if (position.liquidity == 0) return position.fees;
        if (posState.totalLiquidity == 0) return position.fees;

        int128 feePerLiq0 = int128(int256(FullMath.mulDiv(uint256(globalFees0), uint256(1e18), uint256(posState.totalLiquidity))));
        int128 feePerLiq1 = int128(int256(FullMath.mulDiv(uint256(globalFees1), uint256(1e18), uint256(posState.totalLiquidity))));
        
        BalanceDelta newTotalFeePerLiquidity = posState.feePerLiquidity + toBalanceDelta(feePerLiq0, feePerLiq1);
        BalanceDelta feeDiff = newTotalFeePerLiquidity - position.lastFeePerLiquidity;
        
        int128 userFee0 = feeDiff.amount0() >= 0
            ? int128(int256(FullMath.mulDiv(uint256(uint128(feeDiff.amount0())), uint256(position.liquidity), uint256(1e18))))
            : -int128(int256(FullMath.mulDiv(uint256(uint128(-feeDiff.amount0())), uint256(position.liquidity), uint256(1e18))));
        int128 userFee1 = feeDiff.amount1() >= 0
            ? int128(int256(FullMath.mulDiv(uint256(uint128(feeDiff.amount1())), uint256(position.liquidity), uint256(1e18))))
            : -int128(int256(FullMath.mulDiv(uint256(uint128(-feeDiff.amount1())), uint256(position.liquidity), uint256(1e18))));
        
        return position.fees + toBalanceDelta(userFee0, userFee1);
    }


    // Add position to tick-based storage using TickBitmap library
    function addPositionToTick(
        mapping(PoolId => mapping(int24 => bytes32)) storage positionAtTick,
        mapping(PoolId => mapping(int16 => uint256)) storage tickBitmap,
        PoolKey memory key,
        int24 executableTick,
        bytes32 positionKey
    ) internal {
        PoolId poolId = key.toId();
        
        int24 compressedTick = TickBitmap.compress(executableTick, key.tickSpacing);
        
        positionAtTick[poolId][executableTick] = positionKey;
        
        (int16 wordPos, uint8 bitPos) = TickBitmap.position(compressedTick);
        
        uint256 mask = 1 << bitPos;
        tickBitmap[poolId][wordPos] |= mask;
    }


    function removePositionFromTick(
        mapping(PoolId => mapping(int24 => bytes32)) storage positionAtTick,
        mapping(PoolId => mapping(int16 => uint256)) storage tickBitmap,
        PoolKey memory key,
        int24 executableTick
    ) internal {
        PoolId poolId = key.toId();
        
        int24 compressedTick = TickBitmap.compress(executableTick, key.tickSpacing);
        (int16 wordPos, uint8 bitPos) = TickBitmap.position(compressedTick);
        
        uint256 mask = ~(1 << bitPos);
        tickBitmap[poolId][wordPos] &= mask;
        
        positionAtTick[poolId][executableTick] = bytes32(0);
    }



    function calculatePositionFee(
        PoolId poolId,
        int24 bottomTick,
        int24 topTick,
        IPoolManager poolManager
    ) public view returns (uint256 fee0, uint256 fee1) {
        (uint128 liquidityBefore, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128) = 
            StateLibrary.getPositionInfo(
                poolManager,
                poolId,
                address(this),
                bottomTick,
                topTick,
                bytes32(0) // salt
            );

        (uint256 feeGrowthInside0X128, uint256 feeGrowthInside1X128) = StateLibrary.getFeeGrowthInside(
            poolManager,
            poolId,
            bottomTick,
            topTick
        );

        uint256 feeGrowthDelta0 = 0;
        uint256 feeGrowthDelta1 = 0;

        unchecked {
            if (feeGrowthInside0X128 != feeGrowthInside0LastX128) {
                feeGrowthDelta0 = feeGrowthInside0X128 - feeGrowthInside0LastX128;
            }
            if (feeGrowthInside1X128 != feeGrowthInside1LastX128) {
                feeGrowthDelta1 = feeGrowthInside1X128 - feeGrowthInside1LastX128;
            }
            fee0 = FullMath.mulDiv(feeGrowthDelta0, liquidityBefore, Q128);
            fee1 = FullMath.mulDiv(feeGrowthDelta1, liquidityBefore, Q128); 
        }

        return (fee0, fee1);
    }

    /// @notice Decodes a position key into its component parts
    /// @param positionKey The bytes32 key to decode
    /// @return bottomTick The lower tick boundary
    /// @return topTick The upper tick boundary
    /// @return isToken0 Whether the position is for token0
    /// @return nonce The nonce value used in the key
    function decodePositionKey(
        bytes32 positionKey
    ) public pure returns (
        int24 bottomTick,
        int24 topTick,
        bool isToken0,
        uint256 nonce
    ) {
        bottomTick = int24(uint24(uint256(positionKey) >> 232));
        topTick = int24(uint24(uint256(positionKey) >> 208));
        nonce = uint256(positionKey >> 8) & ((1 << 200) - 1);
        isToken0 = uint256(positionKey) & 1 == 1;
    }

    /// @notice Calculates the balance delta for a position based on its key
    /// @param positionKey The unique identifier of the position
    /// @param liquidity The position's liquidity amount
    /// @return BalanceDelta The calculated balance delta
    function getBalanceDelta(
        bytes32 positionKey,
        uint128 liquidity
    ) public pure returns (BalanceDelta) {
        (int24 bottomTick, int24 topTick, bool isToken0,) = decodePositionKey(positionKey);
        
        uint160 sqrtPriceAX96 = TickMath.getSqrtPriceAtTick(bottomTick);
        uint160 sqrtPriceBX96 = TickMath.getSqrtPriceAtTick(topTick);
        
        if (isToken0) {
            // Position was in token0, executed at topTick, got token1
            uint256 amount = LiquidityAmounts.getAmount1ForLiquidity(
                sqrtPriceAX96,
                sqrtPriceBX96,
                liquidity
            );
            return toBalanceDelta(0, int128(int256(amount)));
        } else {
            // Position was in token1, executed at bottomTick, got token0
            uint256 amount = LiquidityAmounts.getAmount0ForLiquidity(
                sqrtPriceAX96,
                sqrtPriceBX96,
                liquidity
            );
            return toBalanceDelta(int128(int256(amount)), 0);
        }
    }
    


    /// @notice Generates unique keys for position identification
    /// @return baseKey Key without nonce for tracking position versions
    /// @return positionKey Unique key including nonce for this specific position
    function getPositionKeys(
        mapping(PoolId => mapping(bytes32 => uint256)) storage currentNonce,
        PoolId poolId,
        int24 bottomTick, 
        int24 topTick,
        bool isToken0
    ) internal view returns (bytes32 baseKey, bytes32 positionKey) {
        // Generate base key combining bottomTick, topTick, and isToken0
        baseKey = bytes32(
            uint256(uint24(bottomTick)) << 232 |
            uint256(uint24(topTick)) << 208 |
            uint256(isToken0 ? 1 : 0)
        );
        
        // Generate full position key with nonce
        positionKey = bytes32(
            uint256(uint24(bottomTick)) << 232 |
            uint256(uint24(topTick)) << 208 |
            uint256(currentNonce[poolId][baseKey]) << 8 |
            uint256(isToken0 ? 1 : 0)
        );
    }    

    function calculateScaledFeePerLiquidity(
        BalanceDelta feeDelta, 
        uint128 liquidity
    ) public pure returns (BalanceDelta) {
        if(feeDelta == BalanceDelta.wrap(0) || liquidity == 0) return BalanceDelta.wrap(0);
        
        return toBalanceDelta(
            feeDelta.amount0() >= 0 
                ? int128(int256(FullMath.mulDiv(uint256(uint128(feeDelta.amount0())), 1e18, liquidity)))
                : -int128(int256(FullMath.mulDiv(uint256(uint128(-feeDelta.amount0())), 1e18, liquidity))),
            feeDelta.amount1() >= 0 
                ? int128(int256(FullMath.mulDiv(uint256(uint128(feeDelta.amount1())), 1e18, liquidity)))
                : -int128(int256(FullMath.mulDiv(uint256(uint128(-feeDelta.amount1())), 1e18, liquidity)))
        );
    }

    function calculateScaledUserFee(
        BalanceDelta feeDiff, 
        uint128 liquidity
    ) public pure returns (BalanceDelta) {
        if(feeDiff == BalanceDelta.wrap(0) || liquidity == 0) return BalanceDelta.wrap(0);
        
        return toBalanceDelta(
            feeDiff.amount0() >= 0 
                ? int128(int256(FullMath.mulDiv(uint256(uint128(feeDiff.amount0())), uint256(liquidity), 1e18)))
                : -int128(int256(FullMath.mulDiv(uint256(uint128(-feeDiff.amount0())), uint256(liquidity), 1e18))),
            feeDiff.amount1() >= 0 
                ? int128(int256(FullMath.mulDiv(uint256(uint128(feeDiff.amount1())), uint256(liquidity), 1e18)))
                : -int128(int256(FullMath.mulDiv(uint256(uint128(-feeDiff.amount1())), uint256(liquidity), 1e18)))
        );
    }
}