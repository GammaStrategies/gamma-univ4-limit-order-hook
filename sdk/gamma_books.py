import web3
import copy
import numpy as np
from eth_utils import to_hex
import matplotlib.pyplot as plt

#abis
manager_abi='''[{"inputs":[{"internalType":"address","name":"_poolManagerAddr","type":"address"},{"internalType":"address","name":"_treasury","type":"address"},{"internalType":"address","name":"_owner","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"address","name":"target","type":"address"}],"name":"AddressEmptyCode","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"AddressInsufficientBalance","type":"error"},{"inputs":[],"name":"AddressZero","type":"error"},{"inputs":[],"name":"AmountTooLow","type":"error"},{"inputs":[],"name":"EnforcedPause","type":"error"},{"inputs":[],"name":"ExpectedPause","type":"error"},{"inputs":[],"name":"FailedInnerCall","type":"error"},{"inputs":[],"name":"FeePercentageTooHigh","type":"error"},{"inputs":[],"name":"MaxOrdersExceeded","type":"error"},{"inputs":[{"internalType":"uint256","name":"provided","type":"uint256"},{"internalType":"uint256","name":"minimum","type":"uint256"}],"name":"MinimumAmountNotMet","type":"error"},{"inputs":[],"name":"NotAuthorized","type":"error"},{"inputs":[],"name":"NotWhitelistedPool","type":"error"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"OwnableInvalidOwner","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"OwnableUnauthorizedAccount","type":"error"},{"inputs":[],"name":"PositionIsWaitingForKeeper","type":"error"},{"inputs":[],"name":"ReentrancyGuardReentrantCall","type":"error"},{"inputs":[{"internalType":"address","name":"token","type":"address"}],"name":"SafeERC20FailedOperation","type":"error"},{"inputs":[],"name":"UnknownCallbackType","type":"error"},{"inputs":[],"name":"ZeroLimit","type":"error"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"Currency","name":"currency","type":"address"},{"indexed":false,"internalType":"address","name":"originalRecipient","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"FailedTransferSentToTreasury","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"uint256","name":"percentage","type":"uint256"}],"name":"HookFeePercentageUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"positionKey","type":"bytes32"},{"indexed":false,"internalType":"int24","name":"bottomTick","type":"int24"},{"indexed":false,"internalType":"int24","name":"topTick","type":"int24"},{"indexed":false,"internalType":"int24","name":"currentTick","type":"int24"}],"name":"KeeperWaitingStatusReset","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"orderOwner","type":"address"},{"indexed":true,"internalType":"PoolId","name":"poolId","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"positionKey","type":"bytes32"}],"name":"OrderCanceled","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"PoolId","name":"poolId","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"positionKey","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"principal0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"principal1","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"fees0","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"fees1","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"hookFeePercentage","type":"uint256"}],"name":"OrderClaimed","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"user","type":"address"},{"indexed":true,"internalType":"PoolId","name":"poolId","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"positionKey","type":"bytes32"}],"name":"OrderCreated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"PoolId","name":"poolId","type":"bytes32"},{"indexed":false,"internalType":"bytes32","name":"positionKey","type":"bytes32"}],"name":"OrderExecuted","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"account","type":"address"}],"name":"Paused","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"PoolId","name":"poolId","type":"bytes32"},{"indexed":false,"internalType":"bytes32[]","name":"leftoverPositions","type":"bytes32[]"}],"name":"PositionsLeftOver","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"account","type":"address"}],"name":"Unpaused","type":"event"},{"inputs":[],"name":"FEE_DENOMINATOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"ZERO_DELTA","outputs":[{"internalType":"BalanceDelta","name":"","type":"int256"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"uint256","name":"offset","type":"uint256"},{"internalType":"uint256","name":"limit","type":"uint256"}],"name":"cancelBatchOrders","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"bytes32","name":"positionKey","type":"bytes32"}],"name":"cancelOrder","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"bytes32[]","name":"positionKeys","type":"bytes32[]"}],"name":"cancelPositionKeys","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"uint256","name":"offset","type":"uint256"},{"internalType":"uint256","name":"limit","type":"uint256"}],"name":"claimBatchOrders","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"bytes32","name":"positionKey","type":"bytes32"}],"name":"claimOrder","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"bytes32[]","name":"positionKeys","type":"bytes32[]"}],"name":"claimPositionKeys","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bool","name":"isToken0","type":"bool"},{"internalType":"int24","name":"targetTick","type":"int24"},{"internalType":"uint256","name":"amount","type":"uint256"},{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"}],"name":"createLimitOrder","outputs":[{"components":[{"internalType":"uint256","name":"usedAmount","type":"uint256"},{"internalType":"bool","name":"isToken0","type":"bool"},{"internalType":"int24","name":"bottomTick","type":"int24"},{"internalType":"int24","name":"topTick","type":"int24"}],"internalType":"struct ILimitOrderManager.CreateOrderResult","name":"","type":"tuple"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"bool","name":"isToken0","type":"bool"},{"internalType":"int24","name":"bottomTick","type":"int24"},{"internalType":"int24","name":"topTick","type":"int24"},{"internalType":"uint256","name":"totalAmount","type":"uint256"},{"internalType":"uint256","name":"totalOrders","type":"uint256"},{"internalType":"uint256","name":"sizeSkew","type":"uint256"},{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"}],"name":"createScaleOrders","outputs":[{"components":[{"internalType":"uint256","name":"usedAmount","type":"uint256"},{"internalType":"bool","name":"isToken0","type":"bool"},{"internalType":"int24","name":"bottomTick","type":"int24"},{"internalType":"int24","name":"topTick","type":"int24"}],"internalType":"struct ILimitOrderManager.CreateOrderResult[]","name":"results","type":"tuple[]"}],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"PoolId","name":"","type":"bytes32"},{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"currentNonce","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"bytes32[]","name":"positionKeys","type":"bytes32[]"},{"internalType":"address","name":"user","type":"address"}],"name":"emergencyCancelOrders","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"executablePositionsLimit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"int24","name":"tickBeforeSwap","type":"int24"},{"internalType":"int24","name":"tickAfterSwap","type":"int24"},{"internalType":"bool","name":"zeroForOne","type":"bool"}],"name":"executeOrder","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"bytes32[]","name":"waitingPositions","type":"bytes32[]"}],"name":"executeOrderByKeeper","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"PoolId","name":"poolId","type":"bytes32"}],"name":"getUserPositionCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"uint256","name":"offset","type":"uint256"},{"internalType":"uint256","name":"limit","type":"uint256"}],"name":"getUserPositions","outputs":[{"components":[{"internalType":"uint128","name":"liquidity","type":"uint128"},{"internalType":"BalanceDelta","name":"fees","type":"int256"},{"internalType":"bytes32","name":"positionKey","type":"bytes32"}],"internalType":"struct ILimitOrderManager.PositionInfo[]","name":"positions","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"hook","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"hook_fee_percentage","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"isKeeper","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"},{"internalType":"bytes32[]","name":"positionKeys","type":"bytes32[]"},{"internalType":"address","name":"user","type":"address"}],"name":"keeperClaimPositionKeys","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"maxOrderLimit","outputs":[{"internalType":"uint24","name":"","type":"uint24"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"Currency","name":"","type":"address"}],"name":"minAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"paused","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"poolManager","outputs":[{"internalType":"contract IPoolManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"","type":"bytes32"},{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"positionState","outputs":[{"internalType":"BalanceDelta","name":"feePerLiquidity","type":"int256"},{"internalType":"uint128","name":"totalLiquidity","type":"uint128"},{"internalType":"bool","name":"isActive","type":"bool"},{"internalType":"bool","name":"isWaitingKeeper","type":"bool"},{"internalType":"uint256","name":"currentNonce","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_limit","type":"uint256"}],"name":"setExecutablePositionsLimit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_hook","type":"address"}],"name":"setHook","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_percentage","type":"uint256"}],"name":"setHookFeePercentage","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_keeper","type":"address"},{"internalType":"bool","name":"_isKeeper","type":"bool"}],"name":"setKeeper","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint24","name":"_limit","type":"uint24"}],"name":"setMaxOrderLimit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"},{"internalType":"uint256","name":"_minAmount","type":"uint256"}],"name":"setMinAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"bool","name":"isWhitelisted","type":"bool"}],"name":"setWhitelistedPool","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"PoolId","name":"","type":"bytes32"},{"internalType":"int24","name":"","type":"int24"}],"name":"token0PositionAtTick","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"","type":"bytes32"},{"internalType":"int16","name":"","type":"int16"}],"name":"token0TickBitmap","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"","type":"bytes32"},{"internalType":"int24","name":"","type":"int24"}],"name":"token1PositionAtTick","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"","type":"bytes32"},{"internalType":"int16","name":"","type":"int16"}],"name":"token1TickBitmap","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"treasury","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes","name":"data","type":"bytes"}],"name":"unlockCallback","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"unpause","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"PoolId","name":"","type":"bytes32"},{"internalType":"bytes32","name":"","type":"bytes32"},{"internalType":"address","name":"","type":"address"}],"name":"userPositions","outputs":[{"internalType":"uint128","name":"liquidity","type":"uint128"},{"internalType":"BalanceDelta","name":"lastFeePerLiquidity","type":"int256"},{"internalType":"BalanceDelta","name":"claimablePrincipal","type":"int256"},{"internalType":"BalanceDelta","name":"fees","type":"int256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"","type":"bytes32"}],"name":"whitelistedPool","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"}]'''
lens_abi='''[{"inputs":[{"internalType":"address","name":"_limitOrderManagerAddr","type":"address"},{"internalType":"address","name":"_owner","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"uint256","name":"totalOrders","type":"uint256"},{"internalType":"uint256","name":"minOrders","type":"uint256"}],"name":"InsufficientOrders","type":"error"},{"inputs":[],"name":"InvalidScaleParameters","type":"error"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"minAmount","type":"uint256"}],"name":"MinAmountNotMet","type":"error"},{"inputs":[{"internalType":"uint256","name":"totalOrders","type":"uint256"},{"internalType":"uint256","name":"maxOrderLimit","type":"uint256"}],"name":"OrderLimitExceeded","type":"error"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"OwnableInvalidOwner","type":"error"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"OwnableUnauthorizedAccount","type":"error"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"}],"name":"PoolKeyNotFound","type":"error"},{"inputs":[{"internalType":"int24","name":"bottomTick","type":"int24"},{"internalType":"int24","name":"topTick","type":"int24"},{"internalType":"int24","name":"minTickRange","type":"int24"}],"name":"TickRangeTooSmall","type":"error"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[],"name":"MIN_ORDERS","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"ZERO_DELTA","outputs":[{"internalType":"BalanceDelta","name":"","type":"int256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"}],"name":"addPoolId","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"totalAmount","type":"uint256"},{"internalType":"uint256","name":"totalOrders","type":"uint256"},{"internalType":"uint256","name":"sizeSkew","type":"uint256"}],"name":"calculateOrderSizes","outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"bytes32","name":"positionKey","type":"bytes32"}],"name":"decodePositionKey","outputs":[{"internalType":"int24","name":"bottomTick","type":"int24"},{"internalType":"int24","name":"topTick","type":"int24"},{"internalType":"bool","name":"isToken0","type":"bool"},{"internalType":"uint256","name":"nonce","type":"uint256"}],"stateMutability":"pure","type":"function"},{"inputs":[],"name":"getAllPools","outputs":[{"components":[{"internalType":"bytes32","name":"poolId","type":"bytes32"},{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"poolKey","type":"tuple"},{"internalType":"string","name":"token0Symbol","type":"string"},{"internalType":"string","name":"token1Symbol","type":"string"}],"internalType":"struct PoolStruct[]","name":"pools","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getAllUserPositions","outputs":[{"components":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"bytes32","name":"positionKey","type":"bytes32"},{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"string","name":"token0Symbol","type":"string"},{"internalType":"string","name":"token1Symbol","type":"string"},{"internalType":"uint8","name":"token0Decimals","type":"uint8"},{"internalType":"uint8","name":"token1Decimals","type":"uint8"},{"internalType":"bool","name":"isToken0","type":"bool"},{"internalType":"int24","name":"bottomTick","type":"int24"},{"internalType":"int24","name":"topTick","type":"int24"},{"internalType":"int24","name":"currentTick","type":"int24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"string","name":"orderType","type":"string"},{"internalType":"uint160","name":"sqrtPrice","type":"uint160"},{"internalType":"uint160","name":"sqrtPriceBottomTick","type":"uint160"},{"internalType":"uint160","name":"sqrtPriceTopTick","type":"uint160"},{"internalType":"uint128","name":"liquidity","type":"uint128"},{"internalType":"uint256","name":"positionToken0Principal","type":"uint256"},{"internalType":"uint256","name":"positionToken1Principal","type":"uint256"},{"internalType":"uint256","name":"positionFeeRevenue0","type":"uint256"},{"internalType":"uint256","name":"positionFeeRevenue1","type":"uint256"},{"internalType":"uint256","name":"totalCurrentToken0Principal","type":"uint256"},{"internalType":"uint256","name":"totalCurrentToken1Principal","type":"uint256"},{"internalType":"uint256","name":"feeRevenue0","type":"uint256"},{"internalType":"uint256","name":"feeRevenue1","type":"uint256"},{"internalType":"uint256","name":"totalToken0AtExecution","type":"uint256"},{"internalType":"uint256","name":"totalToken1AtExecution","type":"uint256"},{"internalType":"uint256","name":"orderSize","type":"uint256"},{"internalType":"bool","name":"claimable","type":"bool"}],"internalType":"struct DetailedUserPosition[]","name":"allPositions","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"uint256","name":"offset","type":"uint256"},{"internalType":"uint256","name":"limit","type":"uint256"}],"name":"getCancellablePositions","outputs":[{"internalType":"bytes32[]","name":"positionKeys","type":"bytes32[]"},{"internalType":"uint256","name":"count","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"uint256","name":"offset","type":"uint256"},{"internalType":"uint256","name":"limit","type":"uint256"}],"name":"getClaimablePositions","outputs":[{"internalType":"bytes32[]","name":"positionKeys","type":"bytes32[]"},{"internalType":"uint256","name":"count","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"Currency","name":"currency","type":"address"}],"name":"getMinAmount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"bool","name":"isToken0","type":"bool"}],"name":"getMinAndMaxTickForLimitOrders","outputs":[{"internalType":"int24","name":"minTick","type":"int24"},{"internalType":"int24","name":"maxTick","type":"int24"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"bool","name":"isToken0","type":"bool"}],"name":"getMinAndMaxTickForScaleOrders","outputs":[{"internalType":"int24","name":"minTick","type":"int24"},{"internalType":"int24","name":"maxTick","type":"int24"}],"stateMutability":"view","type":"function"},{"inputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"}],"name":"getPoolId","outputs":[{"internalType":"PoolId","name":"","type":"bytes32"}],"stateMutability":"pure","type":"function"},{"inputs":[{"internalType":"uint256","name":"index","type":"uint256"}],"name":"getPoolIdAt","outputs":[{"internalType":"PoolId","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"}],"name":"getPoolKey","outputs":[{"components":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"internalType":"struct PoolKey","name":"key","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"bytes32","name":"positionKey","type":"bytes32"}],"name":"getPositionBalances","outputs":[{"components":[{"internalType":"uint256","name":"principal0","type":"uint256"},{"internalType":"uint256","name":"principal1","type":"uint256"},{"internalType":"uint256","name":"fees0","type":"uint256"},{"internalType":"uint256","name":"fees1","type":"uint256"}],"internalType":"struct ILimitOrderManager.PositionBalances","name":"balances","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"uint24","name":"numTicks","type":"uint24"}],"name":"getTickInfosAroundCurrent","outputs":[{"internalType":"int24","name":"currentTick","type":"int24"},{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"components":[{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint160","name":"sqrtPrice","type":"uint160"},{"internalType":"uint256","name":"token0Amount","type":"uint256"},{"internalType":"uint256","name":"token1Amount","type":"uint256"},{"internalType":"uint256","name":"totalTokenAmountsinToken1","type":"uint256"}],"internalType":"struct LimitOrderLens.TickInfo[]","name":"tickInfos","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"PoolId","name":"poolId","type":"bytes32"}],"name":"getUserPositionCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"getUserPositionCountsAcrossPools","outputs":[{"components":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"uint256","name":"count","type":"uint256"}],"internalType":"struct LimitOrderLens.PoolPositionCount[]","name":"counts","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"uint256","name":"offset","type":"uint256"},{"internalType":"uint256","name":"limit","type":"uint256"}],"name":"getUserPositionsPaginated","outputs":[{"components":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"bytes32","name":"positionKey","type":"bytes32"},{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"string","name":"token0Symbol","type":"string"},{"internalType":"string","name":"token1Symbol","type":"string"},{"internalType":"uint8","name":"token0Decimals","type":"uint8"},{"internalType":"uint8","name":"token1Decimals","type":"uint8"},{"internalType":"bool","name":"isToken0","type":"bool"},{"internalType":"int24","name":"bottomTick","type":"int24"},{"internalType":"int24","name":"topTick","type":"int24"},{"internalType":"int24","name":"currentTick","type":"int24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"string","name":"orderType","type":"string"},{"internalType":"uint160","name":"sqrtPrice","type":"uint160"},{"internalType":"uint160","name":"sqrtPriceBottomTick","type":"uint160"},{"internalType":"uint160","name":"sqrtPriceTopTick","type":"uint160"},{"internalType":"uint128","name":"liquidity","type":"uint128"},{"internalType":"uint256","name":"positionToken0Principal","type":"uint256"},{"internalType":"uint256","name":"positionToken1Principal","type":"uint256"},{"internalType":"uint256","name":"positionFeeRevenue0","type":"uint256"},{"internalType":"uint256","name":"positionFeeRevenue1","type":"uint256"},{"internalType":"uint256","name":"totalCurrentToken0Principal","type":"uint256"},{"internalType":"uint256","name":"totalCurrentToken1Principal","type":"uint256"},{"internalType":"uint256","name":"feeRevenue0","type":"uint256"},{"internalType":"uint256","name":"feeRevenue1","type":"uint256"},{"internalType":"uint256","name":"totalToken0AtExecution","type":"uint256"},{"internalType":"uint256","name":"totalToken1AtExecution","type":"uint256"},{"internalType":"uint256","name":"orderSize","type":"uint256"},{"internalType":"bool","name":"claimable","type":"bool"}],"internalType":"struct DetailedUserPosition[]","name":"positions","type":"tuple[]"},{"internalType":"uint256","name":"totalCount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"limitOrderManager","outputs":[{"internalType":"contract LimitOrderManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"int24","name":"bottomTick","type":"int24"},{"internalType":"int24","name":"topTick","type":"int24"}],"name":"minAndMaxScaleOrders","outputs":[{"internalType":"uint256","name":"minOrders","type":"uint256"},{"internalType":"uint256","name":"maxOrders","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"","type":"bytes32"}],"name":"poolIdToKey","outputs":[{"internalType":"Currency","name":"currency0","type":"address"},{"internalType":"Currency","name":"currency1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"},{"internalType":"contract IHooks","name":"hooks","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"poolManager","outputs":[{"internalType":"contract IPoolManager","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"}],"name":"removePoolId","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"PoolId","name":"poolId","type":"bytes32"},{"internalType":"bool","name":"isToken0","type":"bool"},{"internalType":"uint256","name":"totalAmount","type":"uint256"},{"internalType":"uint256","name":"totalOrders","type":"uint256"},{"internalType":"uint256","name":"sizeSkew","type":"uint256"}],"name":"verifyOrderSizes","outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"}],"stateMutability":"view","type":"function"}]'''
token_abi='''[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"guy","type":"address"},{"name":"wad","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"src","type":"address"},{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"wad","type":"uint256"}],"name":"withdraw","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"dst","type":"address"},{"name":"wad","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[],"name":"deposit","outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"","type":"address"},{"name":"","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"payable":true,"stateMutability":"payable","type":"fallback"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"guy","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"dst","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Deposit","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"src","type":"address"},{"indexed":false,"name":"wad","type":"uint256"}],"name":"Withdrawal","type":"event"}]'''

#mapping
mapping={'base':{'rpc_url':'https://mainnet.base.org','manager_address':'0xC7dFb6A0109952f0116413662E1795B44D7BE3c1','lens_address':'0xb9b7e1ad0d1aBba7Cf0Bf23D0Ee1f8a7513e473E','native_token_symbol':'ETH'},
         'unichain':{'rpc_url':'https://unichain.drpc.org','manager_address':'0x8a79bE4DBde8D6496578721B48eE0fEB71De29ee','lens_address':'0x5c1CBa004BbCA0B328Ebf80e6988F2C6B4892F85','native_token_symbol':'ETH'}}

class client:

    def __init__(self,network_name,wallet_key):

        self.wallet_key=wallet_key
        self.wallet_address=web3.Account.from_key(wallet_key).address
        self.network_instance=web3.Web3(web3.Web3.HTTPProvider(mapping.get(network_name)['rpc_url']))
        self.manager_address=mapping.get(network_name)['manager_address']
        self.manager_contract=self.network_instance.eth.contract(address=self.manager_address,abi=manager_abi)
        self.lens_address=mapping.get(network_name)['lens_address']
        self.lens_contract=self.network_instance.eth.contract(address=self.lens_address,abi=lens_abi)
        self.native_token_symbol=mapping.get(network_name)['native_token_symbol']

    def get_pools(self):

        output=self.lens_contract.functions.getAllPools().call()

        pools=[{'pool_id':to_hex(pool[0]),
                'base_token_symbol':{'NATIVE':self.native_token_symbol}.get(pool[2],pool[2]),
                'quote_token_symbol':{'NATIVE':self.native_token_symbol}.get(pool[3],pool[3]),
                'base_token_address':pool[1][0],
                'quote_token_address':pool[1][1],
                'fee':{8388608:'dynamic'}.get(pool[1][2],pool[1][2]/10**6),
                'spacing':pool[1][3]} for pool in output]

        return pools

    def get_book(self,pool_id,invert,window):

        pool_key=self.lens_contract.functions.getPoolKey(pool_id).call()

        base_token_address=pool_key[0]
        quote_token_address=pool_key[1]
        spacing=pool_key[3]

        if base_token_address=='0x0000000000000000000000000000000000000000': base_token_decimals=18
        else: base_token_decimals=self.network_instance.eth.contract(address=base_token_address,abi=token_abi).functions.decimals().call()
        if quote_token_address=='0x0000000000000000000000000000000000000000': quote_token_decimals=18
        else: quote_token_decimals=self.network_instance.eth.contract(address=quote_token_address,abi=token_abi).functions.decimals().call()

        window_formatted=min(10000//spacing*spacing,int(np.log(1+max(0.05,window))/np.log(1.0001))//spacing*spacing)

        output=self.lens_contract.functions.getTickInfosAroundCurrent(pool_id,window_formatted).call()

        tick=output[0]
        book=output[2]

        price=1.0001**tick/10**(quote_token_decimals-base_token_decimals)
        bids=sorted([{'price':1.0001**item[0]/10**(quote_token_decimals-base_token_decimals),'quantity':item[3]/10**quote_token_decimals} for item in book if item[0]<=tick],key=lambda x:x['price'],reverse=True)
        asks=[{'price':1.0001**(item[0]+spacing)/10**(quote_token_decimals-base_token_decimals),'quantity':item[2]/10**base_token_decimals} for item in book if tick<item[0]+spacing]

        if invert:
            price=1/price
            bids,asks=[{'price':1/ask['price'],'quantity':ask['quantity']} for ask in asks],[{'price':1/bid['price'],'quantity':bid['quantity']} for bid in bids]

        book={'price':price,'bids':bids,'asks':asks}

        return book

    def plot_book(self,book,cumulative):

        price=book['price']

        book_copy=copy.deepcopy(book)
        bids=book_copy['bids']
        asks=book_copy['asks']

        cumulative_value=0
        for bid in bids:
            bid['value']=bid['quantity']
            cumulative_value+=bid['quantity']
            bid['cumulative_value']=cumulative_value

        cumulative_value=0
        for ask in asks:
            ask['value']=ask['quantity']*price
            cumulative_value+=ask['quantity']*price
            ask['cumulative_value']=cumulative_value

        if cumulative:

            x_bids=[bid['price'] for bid in sorted(bids,key=lambda x:x['price'],reverse=False)]
            y_bids=[bid['cumulative_value'] for bid in sorted(bids,key=lambda x:x['price'],reverse=False)]

            x_asks=[ask['price'] for ask in sorted(asks,key=lambda x:x['price'],reverse=False)]
            y_asks=[ask['cumulative_value'] for ask in sorted(asks,key=lambda x:x['price'],reverse=False)]

            plt.plot(x_bids,y_bids,color='green')
            plt.fill_between(x_bids,y_bids,color='green',alpha=0.3)

            plt.plot(x_asks,y_asks,color='red')
            plt.fill_between(x_asks,y_asks,color='red',alpha=0.3)

            plt.axvline(x=price,linestyle=':',color='black',label='pool')
            plt.xlabel('price')
            plt.ylabel('cumulative value')
            plt.legend(prop={'size':10})
            plt.grid(False)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

        else:

            x_bids=[bid['price'] for bid in sorted(bids,key=lambda x:x['price'],reverse=False)]
            y_bids=[bid['value'] for bid in sorted(bids,key=lambda x:x['price'],reverse=False)]

            x_asks=[ask['price'] for ask in sorted(asks,key=lambda x:x['price'],reverse=False)]
            y_asks=[ask['value'] for ask in sorted(asks,key=lambda x:x['price'],reverse=False)]

            plt.plot(x_bids,y_bids,color='green')
            plt.fill_between(x_bids,y_bids,color='green',alpha=0.3)

            plt.plot(x_asks,y_asks,color='red')
            plt.fill_between(x_asks,y_asks,color='red',alpha=0.3)

            plt.axvline(x=price,linestyle=':',color='black',label='pool')
            plt.xlabel('price')
            plt.ylabel('value')
            plt.legend(prop={'size':10})
            plt.grid(False)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

        return

    def get_extreme_prices(self,pool_id,invert,side):

        pool_key=self.lens_contract.functions.getPoolKey(pool_id).call()

        base_token_address=pool_key[0]
        quote_token_address=pool_key[1]

        if base_token_address=='0x0000000000000000000000000000000000000000': base_token_decimals=18
        else: base_token_decimals=self.network_instance.eth.contract(address=base_token_address,abi=token_abi).functions.decimals().call()
        if quote_token_address=='0x0000000000000000000000000000000000000000': quote_token_decimals=18
        else: quote_token_decimals=self.network_instance.eth.contract(address=quote_token_address,abi=token_abi).functions.decimals().call()

        if invert: side={'buy':'sell','sell':'buy'}.get(side)

        side_formatted={'buy':False,'sell':True}.get(side)

        output=self.lens_contract.functions.getMinAndMaxTickForLimitOrders(pool_id,side_formatted).call()

        minimum_price=1.0001**output[0]/10**(quote_token_decimals-base_token_decimals)
        maximum_price=1.0001**output[1]/10**(quote_token_decimals-base_token_decimals)

        if invert: minimum_price,maximum_price=1/maximum_price,1/minimum_price

        return [minimum_price,maximum_price]

    def get_extreme_counts(self,pool_id,lower_price,upper_price):

        pool_key=self.lens_contract.functions.getPoolKey(pool_id).call()

        base_token_address=pool_key[0]
        quote_token_address=pool_key[1]
        spacing=pool_key[3]

        if base_token_address=='0x0000000000000000000000000000000000000000': base_token_decimals=18
        else: base_token_decimals=self.network_instance.eth.contract(address=base_token_address,abi=token_abi).functions.decimals().call()
        if quote_token_address=='0x0000000000000000000000000000000000000000': quote_token_decimals=18
        else: quote_token_decimals=self.network_instance.eth.contract(address=quote_token_address,abi=token_abi).functions.decimals().call()

        lower_tick=int(np.log(lower_price*10**(quote_token_decimals-base_token_decimals))/np.log(1.0001))
        upper_tick=int(np.log(upper_price*10**(quote_token_decimals-base_token_decimals))/np.log(1.0001))+spacing

        output=self.lens_contract.functions.minAndMaxScaleOrders(pool_id,lower_tick,upper_tick).call()

        minimum_count=output[0]
        maximum_count=output[1]

        return [minimum_count,maximum_count]

    def place_order(self,pool_id,invert,side,size,price):

        pool_key=self.lens_contract.functions.getPoolKey(pool_id).call()

        base_token_address=pool_key[0]
        quote_token_address=pool_key[1]

        if base_token_address=='0x0000000000000000000000000000000000000000': base_token_decimals=18
        else: base_token_decimals=self.network_instance.eth.contract(address=base_token_address,abi=token_abi).functions.decimals().call()
        if quote_token_address=='0x0000000000000000000000000000000000000000': quote_token_decimals=18
        else: quote_token_decimals=self.network_instance.eth.contract(address=quote_token_address,abi=token_abi).functions.decimals().call()

        if invert:
            side={'buy':'sell','sell':'buy'}.get(side)
            price=1/price

        provided_token_address={'sell':base_token_address,'buy':quote_token_address}.get(side)
        provided_token_decimals={'sell':base_token_decimals,'buy':quote_token_decimals}.get(side)

        tick=int(np.log(price*10**(quote_token_decimals-base_token_decimals))/np.log(1.0001))

        side_formatted={'buy':False,'sell':True}.get(side)
        size_formatted=int(size*10**provided_token_decimals)

        if provided_token_address=='0x0000000000000000000000000000000000000000':

            #place
            data=self.manager_contract.functions.createLimitOrder(side_formatted,tick,size_formatted,pool_key).build_transaction({'from':self.wallet_address,'value':size_formatted,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
            signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
            hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
            receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

        else:

            #approve
            data=self.network_instance.eth.contract(address=provided_token_address,abi=token_abi).functions.approve(self.manager_address,size_formatted).build_transaction({'from':self.wallet_address,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
            signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
            hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
            receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

            #place
            data=self.manager_contract.functions.createLimitOrder(side_formatted,tick,size_formatted,pool_key).build_transaction({'from':self.wallet_address,'value':0,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
            signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
            hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
            receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

        return receipt

    def place_orders(self,pool_id,invert,side,size,lower_price,upper_price,count,skew):

        pool_key=self.lens_contract.functions.getPoolKey(pool_id).call()

        base_token_address=pool_key[0]
        quote_token_address=pool_key[1]
        spacing=pool_key[3]

        if base_token_address=='0x0000000000000000000000000000000000000000':base_token_decimals=18
        else: base_token_decimals=self.network_instance.eth.contract(address=base_token_address,abi=token_abi).functions.decimals().call()
        if quote_token_address=='0x0000000000000000000000000000000000000000':quote_token_decimals=18
        else: quote_token_decimals=self.network_instance.eth.contract(address=quote_token_address,abi=token_abi).functions.decimals().call()

        if invert:
            side={'buy':'sell','sell':'buy'}.get(side)
            lower_price,upper_price=1/upper_price,1/lower_price
            skew=1/skew

        provided_token_address={'sell':base_token_address,'buy':quote_token_address}.get(side)
        provided_token_decimals={'sell':base_token_decimals,'buy':quote_token_decimals}.get(side)

        lower_tick=int(np.log(lower_price*10**(quote_token_decimals-base_token_decimals))/np.log(1.0001))-spacing*(side=='sell')
        upper_tick=int(np.log(upper_price*10**(quote_token_decimals-base_token_decimals))/np.log(1.0001))+spacing*(side=='buy')

        side_formatted={'buy':False,'sell':True}.get(side)
        size_formatted=int(size*10**provided_token_decimals)
        skew_formatted=int(skew*10**18)

        if provided_token_address=='0x0000000000000000000000000000000000000000':

            #place
            data=self.manager_contract.functions.createScaleOrders(side_formatted,lower_tick,upper_tick,size_formatted,count,skew_formatted,pool_key).build_transaction({'from':self.wallet_address,'value':size_formatted,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
            signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
            hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
            receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

        else:

            #approve
            data=self.network_instance.eth.contract(address=provided_token_address,abi=token_abi).functions.approve(self.manager_address,size_formatted).build_transaction({'from':self.wallet_address,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
            signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
            hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
            receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

            #place
            data=self.manager_contract.functions.createScaleOrders(side_formatted,lower_tick,upper_tick,size_formatted,count,skew_formatted,pool_key).build_transaction({'from':self.wallet_address,'value':0,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
            signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
            hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
            receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

        return receipt

    def get_orders(self):

        output=self.lens_contract.functions.getUserPositionsPaginated(self.wallet_address,0,0).call()

        orders=[]
        for order in output[0]:
            orders.append({'pool_id':to_hex(order[0]),
                           'order_id':to_hex(order[1]),
                           'side':{True:'sell',False:'buy'}.get(order[8]),
                           'size':order[28]/10**{True:order[6],False:order[7]}.get(order[8]),
                           'lower_price':1.0001**order[9]/10**(order[7]-order[6]),
                           'upper_price':1.0001**order[10]/10**(order[7]-order[6]),
                           'filled':order[29],
                           'principal_base_token':order[18]/10**order[6],
                           'principal_quote_token':order[19]/10**order[7],
                           'fees_base_token':order[20]/10**order[6],
                           'fees_quote_token':order[21]/10**order[7]})

        return orders

    def cancel_order(self,pool_id,order_id):

        pool_key=self.lens_contract.functions.getPoolKey(pool_id).call()

        data=self.manager_contract.functions.cancelOrder(pool_key,order_id).build_transaction({'from':self.wallet_address,'value':0,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
        signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
        hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
        receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

        return receipt

    def claim_order(self,pool_id,order_id):

        pool_key=self.lens_contract.functions.getPoolKey(pool_id).call()

        data=self.manager_contract.functions.claimOrder(pool_key,order_id).build_transaction({'from':self.wallet_address,'value':0,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
        signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
        hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
        receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

        return receipt

    def cancel_orders(self,pool_id):

        pool_key=self.lens_contract.functions.getPoolKey(pool_id).call()

        data=self.manager_contract.functions.cancelBatchOrders(pool_key,0,10000).build_transaction({'from':self.wallet_address,'value':0,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
        signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
        hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
        receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

        return receipt

    def claim_orders(self,pool_id):

        pool_key=self.lens_contract.functions.getPoolKey(pool_id).call()

        data=self.manager_contract.functions.claimBatchOrders(pool_key,0,10000).build_transaction({'from':self.wallet_address,'value':0,'nonce':self.network_instance.eth.get_transaction_count(self.wallet_address)})
        signature=self.network_instance.eth.account.sign_transaction(data,self.wallet_key)
        hash=self.network_instance.eth.send_raw_transaction(signature.raw_transaction)
        receipt=self.network_instance.eth.wait_for_transaction_receipt(hash)

        return receipt