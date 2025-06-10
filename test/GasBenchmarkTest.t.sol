// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "forge-std/console.sol";
import {Deployers} from "@uniswap/v4-core/test/utils/Deployers.sol";
import {PoolSwapTest} from "v4-core/test/PoolSwapTest.sol";
import {IPoolManager} from "v4-core/interfaces/IPoolManager.sol";
import {PoolKey} from "v4-core/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "v4-core/types/PoolId.sol";
import {Currency, CurrencyLibrary} from "v4-core/types/Currency.sol";
import {StateLibrary} from "v4-core/libraries/StateLibrary.sol";
import {TickMath} from "v4-core/libraries/TickMath.sol";
import {LimitOrderHook} from "src/LimitOrderHook.sol";
import {LimitOrderManager} from "src/LimitOrderManager.sol";
import {Hooks} from "v4-core/libraries/Hooks.sol";
import {IHooks} from "v4-core/interfaces/IHooks.sol";
import {IERC20Minimal} from "v4-core/interfaces/external/IERC20Minimal.sol";
import {BalanceDelta} from "v4-core/types/BalanceDelta.sol";
import {LiquidityAmounts} from "@uniswap/v4-core/test/utils/LiquidityAmounts.sol";
import {ILimitOrderManager} from "src/ILimitOrderManager.sol";
import {ModifyLiquidityParams, SwapParams} from "v4-core/types/PoolOperation.sol";
import "../src/TickLibrary.sol";

contract GasBenchmarkTest is Test, Deployers {
    using PoolIdLibrary for PoolKey;
    using CurrencyLibrary for Currency;
    uint256 public HOOK_FEE_PERCENTAGE = 50000;
    uint256 public constant FEE_DENOMINATOR = 100000;
    uint256 internal constant Q128 = 1 << 128;
    LimitOrderHook hook;
    ILimitOrderManager limitOrderManager;
    LimitOrderManager orderManager;
    address public treasury;
    PoolKey poolKey;

    function setUp() public {
        deployFreshManagerAndRouters();
        (currency0, currency1) = deployMintAndApprove2Currencies();

        // Set up treasury address
        treasury = makeAddr("treasury");

        // First deploy the LimitOrderManager
        orderManager = new LimitOrderManager(
            address(manager), // The pool manager from Deployers
            treasury,
            address(this) // This test contract as owner
        );

        // Deploy hook with proper flags
        uint160 flags = uint160(
            Hooks.BEFORE_SWAP_FLAG | 
            Hooks.AFTER_SWAP_FLAG
        );
        address hookAddress = address(flags);

        // Deploy the hook with the LimitOrderManager address
        deployCodeTo(
            "LimitOrderHook.sol",
            abi.encode(address(manager), address(orderManager), address(this)),
            hookAddress
        );
        hook = LimitOrderHook(hookAddress);
        
        // Set the reference to the manager interface
        limitOrderManager = ILimitOrderManager(address(orderManager));
        
        
        limitOrderManager.setExecutablePositionsLimit(5);
        limitOrderManager.setHook(address(hook));

        // Initialize pool with 1:1 price
        (poolKey,) = initPool(currency0, currency1, hook, 3000, SQRT_PRICE_1_1);
        orderManager.setWhitelistedPool(poolKey.toId(), true);

        // Approve tokens to manager
        IERC20Minimal(Currency.unwrap(currency0)).approve(address(limitOrderManager), type(uint256).max);
        IERC20Minimal(Currency.unwrap(currency1)).approve(address(limitOrderManager), type(uint256).max);

        // Add initial liquidity for testing
        modifyLiquidityRouter.modifyLiquidity(
            poolKey,
            ModifyLiquidityParams({
                tickLower: -887220,
                tickUpper: 887220,
                liquidityDelta: 100 ether,
                salt: bytes32(0)
            }),
            ""
        );
    }





    // Helper functions
    function getBasePositionKey(
        int24 bottomTick,
        int24 topTick,
        bool isToken0
    ) internal pure returns (bytes32) {
        return bytes32(
            uint256(uint24(bottomTick)) << 232 |
            uint256(uint24(topTick)) << 208 |
            uint256(isToken0 ? 1 : 0)
        );
    }

    function getPositionKey(        
        int24 bottomTick,
        int24 topTick,
        bool isToken0,
        uint256 nonce
    ) internal pure returns (bytes32) {
        return bytes32(
            uint256(uint24(bottomTick)) << 232 |
            uint256(uint24(topTick)) << 208 |
            uint256(nonce) << 8 |
            uint256(isToken0 ? 1 : 0)
        );
    }

    /// @notice Gas benchmark comparing hooked pool with limit order execution vs vanilla pool
    function test_gas_benchmark_hooked_vs_vanilla_pool_with_execution() public {
        console.log("\n=== Gas Benchmark: Hooked Pool vs Vanilla Pool ===");
        
        // Setup tokens and balances for testing
        deal(Currency.unwrap(currency0), address(this), 200 ether);
        deal(Currency.unwrap(currency1), address(this), 200 ether);
        
        // === Setup Vanilla Pool (No Hooks) ===
        PoolKey memory vanillaPoolKey;
        (vanillaPoolKey,) = initPool(currency0, currency1, IHooks(address(0)), 3000, SQRT_PRICE_1_1);
        
        // Add identical liquidity to vanilla pool
        modifyLiquidityRouter.modifyLiquidity(
            vanillaPoolKey,
            ModifyLiquidityParams({
                tickLower: -887220,
                tickUpper: 887220,
                liquidityDelta: 100 ether,
                salt: bytes32(0)
            }),
            ""
        );
        
        // === Setup Limit Order in Hooked Pool ===
        uint256 sellAmount = 1 ether;
        
        // Get current tick and ensure target is above it with proper spacing
        (, int24 currentTick,,) = StateLibrary.getSlot0(manager, poolKey.toId());
        
        // Calculate target tick properly spaced above current tick
        int24 targetTick = currentTick + poolKey.tickSpacing * 2; // Use 2 tick spacings above
        targetTick = (targetTick / poolKey.tickSpacing) * poolKey.tickSpacing; // Ensure proper spacing
        
        console.log("Current tick:", currentTick);
        console.log("Target tick:", targetTick);
        console.log("Creating limit order at target tick:", targetTick);
        
        // Create limit order that will be executed during swap
        LimitOrderManager.CreateOrderResult memory result = limitOrderManager.createLimitOrder(
            true, // selling token0
            targetTick,
            sellAmount,
            poolKey
        );
        
        console.log("Limit order created:");
        console.log("  Bottom tick:", result.bottomTick);
        console.log("  Top tick:", result.topTick);
        console.log("  Used amount:", result.usedAmount);
        
        // Perform the actual benchmark comparison
        _performSwapBenchmark(vanillaPoolKey, result.topTick);
    }
    
    /// @notice Helper function to perform the swap benchmark and avoid stack too deep
    function _performSwapBenchmark(PoolKey memory vanillaPoolKey, int24 limitOrderTopTick) internal {
        // === Define swap parameters ===
        int24 targetStopTick = 120; // Fixed target tick for both pools
        
        PoolSwapTest.TestSettings memory testSettings = PoolSwapTest.TestSettings({
            takeClaims: false,
            settleUsingBurn: false
        });
        
        console.log("Swap target stop tick:", targetStopTick);
        
        // === Benchmark Vanilla Pool Swap ===
        console.log("\n--- Vanilla Pool Swap ---");
        (, int24 vanillaTickBefore,,) = StateLibrary.getSlot0(manager, vanillaPoolKey.toId());
        console.log("Vanilla - Before swap tick:", vanillaTickBefore);
        
        uint256 vanillaGasStart = gasleft();
        swapRouter.swap(
            vanillaPoolKey,
            SwapParams({
                zeroForOne: false,
                amountSpecified: -1.2 ether,
                sqrtPriceLimitX96: TickMath.getSqrtPriceAtTick(targetStopTick)
            }),
            testSettings,
            ""
        );
        uint256 vanillaGasUsed = vanillaGasStart - gasleft();
        
        (, int24 vanillaTickAfter,,) = StateLibrary.getSlot0(manager, vanillaPoolKey.toId());
        console.log("Vanilla - After swap tick:", vanillaTickAfter);
        console.log("Vanilla pool gas used:", vanillaGasUsed);
        
        // === Benchmark Hooked Pool Swap ===
        console.log("\n--- Hooked Pool Swap (with limit order execution) ---");
        (, int24 hookedTickBefore,,) = StateLibrary.getSlot0(manager, poolKey.toId());
        console.log("Hooked - Before swap tick:", hookedTickBefore);
        
        uint256 hookedGasStart = gasleft();
        swapRouter.swap(
            poolKey,
            SwapParams({
                zeroForOne: false,
                amountSpecified: -2.0 ether, // larger amount to ensure we reach target tick
                sqrtPriceLimitX96: TickMath.getSqrtPriceAtTick(targetStopTick)
            }),
            testSettings,
            ""
        );
        uint256 hookedGasUsed = hookedGasStart - gasleft();
        
        (, int24 hookedTickAfter,,) = StateLibrary.getSlot0(manager, poolKey.toId());
        console.log("Hooked - After swap tick:", hookedTickAfter);
        console.log("Hooked pool gas used:", hookedGasUsed);
        
        // === Verify and display results ===
        _verifyAndDisplayResults(vanillaGasUsed, hookedGasUsed);
    }
    
    /// @notice Helper function to verify results and display gas benchmarks
    function _verifyAndDisplayResults(uint256 vanillaGasUsed, uint256 hookedGasUsed) internal {

        
        // === Calculate and display gas overhead ===
        uint256 gasOverhead = hookedGasUsed - vanillaGasUsed;
        uint256 overheadPercentage = (gasOverhead * 100) / vanillaGasUsed;
        
        console.log("\n=== Gas Benchmark Results ===");
        console.log("Vanilla pool gas:", vanillaGasUsed);
        console.log("Hooked pool gas:", hookedGasUsed);
        console.log("Gas overhead:", gasOverhead);
        console.log("Overhead percentage:", overheadPercentage, "%");
        
        // Assert reasonable gas overhead (should be less than 300% overhead for limit order execution)
        assertLt(overheadPercentage, 300, "Gas overhead too high");
        
        // Ensure hooked pool used more gas (sanity check)
        assertGt(hookedGasUsed, vanillaGasUsed, "Hooked pool should use more gas");
    }

    /// @notice Gas benchmark for multiple limit order executions in a single swap
    function test_gas_benchmark_multiple_limit_orders() public {
        console.log("\n=== Gas Benchmark: Multiple Limit Orders Execution ===");
        
        // Setup tokens and balances
        deal(Currency.unwrap(currency0), address(this), 200 ether);
        deal(Currency.unwrap(currency1), address(this), 200 ether);
        
        // Set higher execution limit for this test
        limitOrderManager.setExecutablePositionsLimit(10);
        
        // Get current tick
        (, int24 currentTick,,) = StateLibrary.getSlot0(manager, poolKey.toId());
        console.log("Current tick:", currentTick);
        
        // Create multiple limit orders at different price levels
        uint256 numOrders = 5;
        int24[] memory targetTicks = new int24[](numOrders);
        
        for (uint256 i = 0; i < numOrders; i++) {
            // Create orders at progressively higher ticks (spaced properly)
            targetTicks[i] = currentTick + poolKey.tickSpacing * int24(uint24(i + 2)); // Start 2 spacings above, then 3, 4, 5, 6
            targetTicks[i] = (targetTicks[i] / poolKey.tickSpacing) * poolKey.tickSpacing; // Ensure proper spacing
            
            console.log("Creating limit order at tick:", targetTicks[i]);
            
            limitOrderManager.createLimitOrder(
                true, // selling token0
                targetTicks[i],
                0.5 ether, // smaller amount per order
                poolKey
            );
        }
        
        // Setup vanilla pool for comparison
        PoolKey memory vanillaPoolKey;
        (vanillaPoolKey,) = initPool(currency0, currency1, IHooks(address(0)), 3000, SQRT_PRICE_1_1);
        
        modifyLiquidityRouter.modifyLiquidity(
            vanillaPoolKey,
            ModifyLiquidityParams({
                tickLower: -887220,
                tickUpper: 887220,
                liquidityDelta: 100 ether,
                salt: bytes32(0)
            }),
            ""
        );
        
        // Define swap that will execute multiple orders
        SwapParams memory swapParams = SwapParams({
            zeroForOne: false,
            amountSpecified: -5 ether, // Large enough to execute multiple orders
            sqrtPriceLimitX96: TickMath.getSqrtPriceAtTick(targetTicks[numOrders - 1] + 100)
        });
        
        PoolSwapTest.TestSettings memory testSettings = PoolSwapTest.TestSettings({
            takeClaims: false,
            settleUsingBurn: false
        });
        
        // Benchmark vanilla pool
        uint256 vanillaGasStart = gasleft();
        swapRouter.swap(vanillaPoolKey, swapParams, testSettings, "");
        uint256 vanillaGasUsed = vanillaGasStart - gasleft();
        
        // Benchmark hooked pool with multiple executions
        uint256 hookedGasStart = gasleft();
        swapRouter.swap(poolKey, swapParams, testSettings, "");
        uint256 hookedGasUsed = hookedGasStart - gasleft();
        

        
        // Calculate results
        uint256 gasOverhead = hookedGasUsed - vanillaGasUsed;
        uint256 gasPerOrder = gasOverhead / numOrders;
        
        console.log("\n=== Multiple Orders Gas Results ===");
        console.log("Number of orders:", numOrders);
        console.log("Vanilla gas:", vanillaGasUsed);
        console.log("Hooked gas:", hookedGasUsed);
        console.log("Total overhead:", gasOverhead);
        console.log("Gas per order:", gasPerOrder);
    }




    /// @notice Gas benchmark comparing hooked pool WITHOUT execution vs vanilla pool (baseline hook overhead)
    function test_gas_benchmark_hooked_vs_vanilla_pool_no_execution() public {
        console.log("\n=== Gas Benchmark: Hooked Pool (No Execution) vs Vanilla Pool ===");
        
        // Setup tokens and balances for testing
        deal(Currency.unwrap(currency0), address(this), 200 ether);
        deal(Currency.unwrap(currency1), address(this), 200 ether);
        
        // === Setup Vanilla Pool (No Hooks) ===
        PoolKey memory vanillaPoolKey;
        (vanillaPoolKey,) = initPool(currency0, currency1, IHooks(address(0)), 3000, SQRT_PRICE_1_1);
        
        // Add identical liquidity to vanilla pool
        modifyLiquidityRouter.modifyLiquidity(
            vanillaPoolKey,
            ModifyLiquidityParams({
                tickLower: -887220,
                tickUpper: 887220,
                liquidityDelta: 100 ether,
                salt: bytes32(0)
            }),
            ""
        );
        
        // Note: NO limit orders created - we want to measure pure hook overhead
        console.log("No limit orders created - measuring baseline hook overhead");
        
        // Perform the actual benchmark comparison
        _performSwapBenchmarkNoExecution(vanillaPoolKey);
    }
    
    /// @notice Helper function to perform swap benchmark without limit order execution
    function _performSwapBenchmarkNoExecution(PoolKey memory vanillaPoolKey) internal {
        // === Define identical swap parameters for both pools ===
        int24 targetStopTick = 120; // Same target for both pools
        
        SwapParams memory swapParams = SwapParams({
            zeroForOne: false, // buying token0 with token1 (price goes up)
            amountSpecified: -1.2 ether, // identical amount for both
            sqrtPriceLimitX96: TickMath.getSqrtPriceAtTick(targetStopTick)
        });
        
        PoolSwapTest.TestSettings memory testSettings = PoolSwapTest.TestSettings({
            takeClaims: false,
            settleUsingBurn: false
        });
        
        console.log("Swap target stop tick:", targetStopTick);
        console.log("Swap amount (identical for both):", swapParams.amountSpecified);
        
        // === Benchmark Vanilla Pool Swap ===
        console.log("\n--- Vanilla Pool Swap ---");
        (, int24 vanillaTickBefore,,) = StateLibrary.getSlot0(manager, vanillaPoolKey.toId());
        console.log("Vanilla - Before swap tick:", vanillaTickBefore);
        
        uint256 vanillaGasStart = gasleft();
        swapRouter.swap(vanillaPoolKey, swapParams, testSettings, "");
        uint256 vanillaGasUsed = vanillaGasStart - gasleft();
        
        (, int24 vanillaTickAfter,,) = StateLibrary.getSlot0(manager, vanillaPoolKey.toId());
        console.log("Vanilla - After swap tick:", vanillaTickAfter);
        console.log("Vanilla pool gas used:", vanillaGasUsed);
        
        // === Benchmark Hooked Pool Swap (no execution expected) ===
        console.log("\n--- Hooked Pool Swap (no limit orders to execute) ---");
        (, int24 hookedTickBefore,,) = StateLibrary.getSlot0(manager, poolKey.toId());
        console.log("Hooked - Before swap tick:", hookedTickBefore);
        
        uint256 hookedGasStart = gasleft();
        swapRouter.swap(poolKey, swapParams, testSettings, "");
        uint256 hookedGasUsed = hookedGasStart - gasleft();
        
        (, int24 hookedTickAfter,,) = StateLibrary.getSlot0(manager, poolKey.toId());
        console.log("Hooked - After swap tick:", hookedTickAfter);
        console.log("Hooked pool gas used:", hookedGasUsed);
        

        
        // === Calculate and display baseline hook overhead ===
        uint256 gasOverhead = hookedGasUsed - vanillaGasUsed;
        uint256 overheadPercentage = vanillaGasUsed > 0 ? (gasOverhead * 100) / vanillaGasUsed : 0;
        
        console.log("\n=== Baseline Hook Overhead Results ===");
        console.log("Vanilla pool gas:", vanillaGasUsed);
        console.log("Hooked pool gas (no execution):", hookedGasUsed);
        console.log("Baseline hook overhead:", gasOverhead);
        console.log("Baseline overhead percentage:", overheadPercentage, "%");
        
        // Verify both pools reached the same tick
        assertEq(vanillaTickAfter, hookedTickAfter, "Both pools should reach the same tick");
        
        // Baseline hook overhead should be minimal (< 50% for just hooks)
        assertLt(overheadPercentage, 50, "Baseline hook overhead should be minimal");
        
        // Ensure hooked pool used more gas (even without execution)
        assertGt(hookedGasUsed, vanillaGasUsed, "Hooked pool should use slightly more gas even without execution");
    }
}