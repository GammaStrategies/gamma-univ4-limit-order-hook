// SPDX-License-Identifier: BSL
pragma solidity ^0.8.24;
import {PoolKey} from "v4-core/types/PoolKey.sol";
import {TickMath} from "v4-core/libraries/TickMath.sol";
import {FullMath} from "v4-core/libraries/FullMath.sol";
import {FixedPoint96} from "v4-core/libraries/FixedPoint96.sol";
import {ILimitOrderManager} from "./ILimitOrderManager.sol";

library TickLibrary {
    error WrongTargetTick(int24 currentTick, int24 targetTick, bool isToken0);
    error BottomTickMustBeGreaterThanCurrentTick(int24 currentTick, int24 bottomTick, bool isToken0);
    error TopTickMustBeLessThanOrEqualToCurrentTick(int24 currentTick, int24 topTick, bool isToken0);
    error RoundedTicksTooClose(int24 currentTick, int24 roundedCurrentTick, int24 targetTick, int24 roundedTargetTick, bool isToken0);
    error RoundedTargetTickLessThanRoundedCurrentTick(int24 currentTick, int24 roundedCurrentTick, int24 targetTick, int24 roundedTargetTick);
    error RoundedTargetTickGreaterThanRoundedCurrentTick(int24 currentTick, int24 roundedCurrentTick, int24 targetTick, int24 roundedTargetTick);
    error WrongTickRange(int24 bottomTick, int24 topTick, int24 currentTick, int24 targetTick, bool isToken0, bool isRange);
    error SingleTickWrongTickRange(int24 bottomTick, int24 topTick, int24 currentTick, int24 targetTick, bool isToken0);
    error TickOutOfBounds(int24 tick);
    error InvalidPrice(uint256 price);
    error PriceMustBeGreaterThanZero();
    error InvalidSizeSkew();
    error MaxOrdersExceeded();
    error InvalidTickRange();
    error MinimumTwoOrders();

    uint256 internal constant Q128 = 1 << 128;

    function maxUsableTick(int24 tickSpacing) internal pure returns (int24) {
        unchecked {
            return (TickMath.MAX_TICK / tickSpacing) * tickSpacing;
        }
    }

    function minUsableTick(int24 tickSpacing) internal pure returns (int24) {
        unchecked {
            return (TickMath.MIN_TICK / tickSpacing) * tickSpacing;
        }
    }

    function getRoundedTargetTick(
        int24 targetTick,
        bool isToken0,
        int24 tickSpacing
    ) internal pure returns(int24 roundedTargetTick) {
        if (isToken0) {
            roundedTargetTick = targetTick >= 0 ? 
                (targetTick / tickSpacing) * tickSpacing :
                ((targetTick % tickSpacing == 0) ? targetTick : ((targetTick / tickSpacing) - 1) * tickSpacing);
        } else {
            roundedTargetTick = targetTick < 0 ?
                (targetTick / tickSpacing) * tickSpacing :
                ((targetTick % tickSpacing == 0) ? targetTick : ((targetTick / tickSpacing) + 1) * tickSpacing);
        }
    }

    function getRoundedCurrentTick(
        int24 currentTick,
        bool isToken0,
        int24 tickSpacing
    ) internal pure returns(int24 roundedCurrentTick) {
        if (isToken0) {
            roundedCurrentTick = currentTick >= 0 ? 
                (currentTick / tickSpacing) * tickSpacing + tickSpacing :
                ((currentTick % tickSpacing == 0) ? currentTick + tickSpacing : (currentTick / tickSpacing) * tickSpacing);
        } else {
            roundedCurrentTick = currentTick >= 0 ?
                (currentTick / tickSpacing) * tickSpacing :
                ((currentTick % tickSpacing == 0) ? currentTick : (currentTick / tickSpacing) * tickSpacing - tickSpacing);
        }
    }
    
    /// @notice Validates and calculates the appropriate tick range for a single-tick limit order
    /// @param currentTick The current market tick price
    /// @param targetTick The target tick price for the order
    /// @param tickSpacing The minimum tick spacing for the pool
    /// @param isToken0 True if order is for token0, false for token1
    /// @return bottomTick The calculated lower tick boundary
    /// @return topTick The calculated upper tick boundary
    function getValidTickRange(
        int24 currentTick,
        int24 targetTick,
        int24 tickSpacing,
        bool isToken0
    ) public pure returns (int24 bottomTick, int24 topTick) {
        if(isToken0 && currentTick >= targetTick)
            revert WrongTargetTick(currentTick, targetTick, true);
        if(!isToken0 && currentTick <= targetTick)
            revert WrongTargetTick(currentTick, targetTick, false);

        int24 roundedTargetTick = getRoundedTargetTick(targetTick, isToken0, tickSpacing);
        int24 roundedCurrentTick = getRoundedCurrentTick(currentTick, isToken0, tickSpacing);

        int24 tickDiff = roundedCurrentTick > roundedTargetTick ?
                        roundedCurrentTick - roundedTargetTick :
                        roundedTargetTick - roundedCurrentTick;
                        
        if(tickDiff < tickSpacing)
            revert RoundedTicksTooClose(currentTick, roundedCurrentTick, targetTick, roundedTargetTick, isToken0);

        if(isToken0) {
            if(roundedCurrentTick >= roundedTargetTick)
                revert RoundedTargetTickLessThanRoundedCurrentTick(currentTick, roundedCurrentTick, targetTick, roundedTargetTick);
            topTick = roundedTargetTick;
            bottomTick = topTick - tickSpacing;
        } else {
            if(roundedCurrentTick <= roundedTargetTick)
                revert RoundedTargetTickGreaterThanRoundedCurrentTick(currentTick, roundedCurrentTick, targetTick, roundedTargetTick);
            bottomTick = roundedTargetTick;
            topTick = bottomTick + tickSpacing;
        }

        if(bottomTick >= topTick)
            revert SingleTickWrongTickRange(bottomTick, topTick, currentTick, targetTick, isToken0);
        
        if (bottomTick < minUsableTick(tickSpacing) || topTick > maxUsableTick(tickSpacing)) 
            revert TickOutOfBounds(targetTick);
    }

    function validateAndPrepareScaleOrders(
        int24 bottomTick,
        int24 topTick,
        int24 currentTick,
        bool isToken0,
        uint256 totalOrders,
        uint256 sizeSkew,
        int24 tickSpacing
    ) public pure returns (ILimitOrderManager.OrderInfo[] memory orders) {
        if (totalOrders < 2) revert MinimumTwoOrders();
        if (bottomTick >= topTick) revert InvalidTickRange();
        if (sizeSkew == 0) revert InvalidSizeSkew();


        if(isToken0 && currentTick >= bottomTick)
            revert BottomTickMustBeGreaterThanCurrentTick(currentTick, bottomTick, true);
        if(!isToken0 && currentTick < topTick)
            revert TopTickMustBeLessThanOrEqualToCurrentTick(currentTick, topTick, false);
        
        // Validate and round ticks 
        if (isToken0) {
            // Rounded bottom tick is always greater or equal to original bottom tick
            bottomTick = bottomTick % tickSpacing == 0 ? bottomTick :
                        bottomTick > 0 ? (bottomTick / tickSpacing + 1) * tickSpacing :
                        (bottomTick / tickSpacing) * tickSpacing;
            topTick = getRoundedTargetTick(topTick, isToken0, tickSpacing);
            require(topTick > bottomTick, "Rounded top tick must be above rounded bottom tick for token0 orders");
        } else {
            // Rounded top tick is always less or equal to original top tick
            topTick = topTick % tickSpacing == 0 ? topTick :
                    topTick > 0 ? (topTick / tickSpacing) * tickSpacing :
                    (topTick / tickSpacing - 1) * tickSpacing;
            bottomTick = getRoundedTargetTick(bottomTick, isToken0, tickSpacing);
            require(bottomTick < topTick, "Rounded bottom tick must be below rounded top tick for token1 orders");
        }

        if (bottomTick < minUsableTick(tickSpacing) || topTick > maxUsableTick(tickSpacing)) 
            revert TickOutOfBounds(bottomTick < minUsableTick(tickSpacing) ? bottomTick : topTick);

        // Check if enough space for orders
        // Handle uint256 to uint24 conversion safely for totalOrders
        if (totalOrders > uint256(uint24((topTick - bottomTick) / tickSpacing)))
            revert MaxOrdersExceeded();

        // Initialize orders array
        orders = new ILimitOrderManager.OrderInfo[](totalOrders);

        // Calculate positions with improved distribution
        int24 effectiveRange = topTick - bottomTick - tickSpacing;
        
        if (isToken0) {
            for (uint256 i = 0; i < totalOrders; i++) {
                // Calculate position
                int24 orderBottomTick;
                if (i == totalOrders - 1) {
                    // Last order approaches max
                    orderBottomTick = topTick - tickSpacing;
                } else {
                    // Proportionally distribute
                    orderBottomTick = bottomTick + int24(uint24((i * uint256(uint24(effectiveRange))) / (totalOrders - 1)));
                    orderBottomTick = orderBottomTick % tickSpacing == 0 ?
                                    orderBottomTick :
                                    orderBottomTick >= 0 ?
                                        orderBottomTick / tickSpacing * tickSpacing + tickSpacing :
                                        orderBottomTick / tickSpacing * tickSpacing;
                }
                
                
                orders[i] = ILimitOrderManager.OrderInfo({
                    bottomTick: orderBottomTick,
                    topTick: orderBottomTick + tickSpacing,
                    amount: 0,
                    liquidity: 0
                });
            }
        } else {
            for (uint256 i = 0; i < totalOrders; i++) {
                // Calculate position
                int24 orderBottomTick;
                if (i == 0) {
                    // First order uses min
                    orderBottomTick = bottomTick;
                } else {
                    // Proportionally distribute
                    orderBottomTick = bottomTick + int24(uint24((i * uint256(uint24(effectiveRange))) / (totalOrders - 1)));
                    orderBottomTick = orderBottomTick % tickSpacing == 0 ?
                                    orderBottomTick :
                                    orderBottomTick >= 0 ?
                                        orderBottomTick / tickSpacing * tickSpacing + tickSpacing :
                                        orderBottomTick / tickSpacing * tickSpacing;
                }
                
                int24 orderTopTick = orderBottomTick + tickSpacing;

                
                orders[i] = ILimitOrderManager.OrderInfo({
                    bottomTick: orderBottomTick,
                    topTick: orderTopTick,
                    amount: 0,
                    liquidity: 0
                });
            }
        }
        
        return orders;
    }

    function getRoundedPrice(
        uint256 price,  //always expressed as token0/token1 price
        PoolKey calldata key,
        bool isToken0
    ) public pure returns (uint256 roundedPrice) {
        // Convert price to sqrtPriceX96
        uint160 targetSqrtPriceX96 = getSqrtPriceFromPrice(price);
        
        // Get raw tick from sqrt price
        int24 rawTargetTick = TickMath.getTickAtSqrtPrice(targetSqrtPriceX96);
        
        // Round the tick according to token direction and spacing
        int24 roundedTargetTick = getRoundedTargetTick(rawTargetTick, isToken0, key.tickSpacing);
        
        // Validate the rounded tick is within bounds
        if (roundedTargetTick < minUsableTick(key.tickSpacing) || 
            roundedTargetTick > maxUsableTick(key.tickSpacing)) {
            revert TickOutOfBounds(roundedTargetTick);
        }
        
        // Get the sqrtPriceX96 at the rounded tick
        uint160 roundedSqrtPriceX96 = TickMath.getSqrtPriceAtTick(roundedTargetTick);
        
        // Convert back to regular price
        roundedPrice = getPriceFromSqrtPrice(roundedSqrtPriceX96);
        
        return roundedPrice;
    }

    function getSqrtPriceFromPrice(uint256 price) public pure returns (uint160) {
        if (price == 0) revert PriceMustBeGreaterThanZero();
        
        // price = token1/token0
        // Convert price to Q96 format first
        uint256 priceQ96 = FullMath.mulDiv(price, FixedPoint96.Q96, 1 ether); // Since input price is in 1e18 format
    
        // Take square root using our sqrt function
        uint256 sqrtPriceX96 = sqrt(priceQ96) << 48;
        
        if (sqrtPriceX96 > type(uint160).max) revert InvalidPrice(price);
        
        return uint160(sqrtPriceX96);
    }

    function getPriceFromSqrtPrice(uint160 sqrtPriceX96) public pure returns (uint256) {
        // Square the sqrt price to get the price in Q96 format
        uint256 priceQ96 = FullMath.mulDiv(uint256(sqrtPriceX96), uint256(sqrtPriceX96), 1 << 96);
        
        // Convert from Q96 to regular price (1e18 format)
        return FullMath.mulDiv(priceQ96, 1 ether, FixedPoint96.Q96);
    }

    function sqrt(uint256 x) public pure returns (uint256 y) {
        uint256 z = (x + 1) / 2;
        y = x;
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
    }
}