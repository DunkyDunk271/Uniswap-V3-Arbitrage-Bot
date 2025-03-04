import math
import struct


def GetAmountReceive(A_supply, B_supply, AmountAtoB):
    #Trade estimation with constant fee - plan use BlockNative fee estimator for dynamic fee
    AmountReceive = (B_supply - (A_supply * B_supply / (A_supply + AmountAtoB))) * 0.997
    return AmountReceive

def ReserveEstimation(PendingTransactions, LiquidityPoolIDs, Uni_USDT_Total_Supply, Uni_WETH_Total_Supply, Sushi_USDT_Total_Supply, Sushi_WETH_Total_Supply):
    for Transaction in PendingTransactions:
        if Transaction.toAddress == LiquidityPoolIDs[0]:
            #Uniswap WETH to USDT
            Uni_USDT_Total_Supply -= GetAmountReceive(Uni_WETH_Total_Supply, Uni_USDT_Total_Supply, float(int(Transaction.value, 16)))
            Uni_WETH_Total_Supply += float(int(Transaction.value, 16))
        elif Transaction.toAddress == LiquidityPoolIDs[1]:
            #Uniswap USDT to WETH
            Uni_USDT_Total_Supply += float(int(Transaction.value, 16))
            Uni_WETH_Total_Supply -= GetAmountReceive(Uni_USDT_Total_Supply, Uni_WETH_Total_Supply, float(int(Transaction.value, 16)))
        elif Transaction.toAddress == LiquidityPoolIDs[2]:
            #Sushiswap WETH to USDT
            Sushi_USDT_Total_Supply -= GetAmountReceive(Sushi_WETH_Total_Supply, Sushi_USDT_Total_Supply, float(int(Transaction.value, 16)))
            Sushi_WETH_Total_Supply += float(int(Transaction.value, 16))
        elif Transaction.toAddress == LiquidityPoolIDs[3]:
            #Sushiswap USDT to WETH
            Sushi_USDT_Total_Supply += float(int(Transaction.value, 16))
            Sushi_WETH_Total_Supply -= GetAmountReceive(Sushi_USDT_Total_Supply, Sushi_WETH_Total_Supply, float(int(Transaction.value, 16)))

    return Sushi_WETH_Total_Supply, Sushi_USDT_Total_Supply, Uni_WETH_Total_Supply, Uni_USDT_Total_Supply

def ArbitrageOpportunitySpot(Sushi_WETH_Total_Supply, Sushi_USDT_Total_Supply, Uni_WETH_Total_Supply, Uni_USDT_Total_Supply):
    Sushi_k = Sushi_WETH_Total_Supply * Sushi_USDT_Total_Supply
    Uni_k = Uni_WETH_Total_Supply * Uni_USDT_Total_Supply
    Sushi_WETH_to_USDT_rate = Sushi_USDT_Total_Supply / Sushi_WETH_Total_Supply
    Sushi_USDT_to_WETH_rate = Sushi_WETH_Total_Supply / Sushi_USDT_Total_Supply
    Uni_WETH_to_USDT_rate = Uni_USDT_Total_Supply / Uni_WETH_Total_Supply
    Uni_USDT_to_WETH_rate = Uni_WETH_Total_Supply / Uni_USDT_Total_Supply

    if Uni_WETH_to_USDT_rate > Sushi_WETH_to_USDT_rate:
        return "UniWETH-USDT/SushiUSDT-WETH"
    elif Uni_USDT_to_WETH_rate > Sushi_USDT_to_WETH_rate:
        return "UniUSDT-WETH/SushiWETH-USDT"
    else:
        return "No Arbitrage Opportunity"

def OptimalArbitrageAmount(ReserveInA, ReserveOutA, ReserveInB, ReserveOutB):
        #Optimal Arbitrage Strategy with constant fee
    '''
    start with WETH - end with more WETH
    r = optimal amount in
    x_a = reserve out of AMM A: Sushi WETH
    y_a = reserve in of AMM A: Sushi USDT
    x_b = reserve in of AMM B: Uni WETH
    y_b = reserve out of AMM B: Uni USDT
    f = fee (0.03%)
    '''
    x_a = ReserveInA
    y_a = ReserveOutA
    x_b = ReserveInB
    y_b = ReserveOutB
    f = 0.003
    k = (1 - f) * x_b + (1 - f)**2 * x_a
    a = k**2
    b = 2 * k * y_a * x_b
    c = (y_a * x_b) ** 2 - (1 - f)**2 * x_a * y_b * y_a * x_b
    

    r = (-b + math.sqrt(b**2 - 4*a*c)) / (2*a)
    ReceivefromA = GetAmountReceive(ReserveInA, ReserveOutA, r)
    profit = (1 - f) * GetAmountReceive(ReserveInB, ReserveOutB, ReceivefromA) - r
    return r, profit


def hex_to_float_struct(hex_str):
    hex_str = hex_str.strip().replace("0x", "")
    byte_array = bytes.fromhex(hex_str)
    float_num = struct.unpack('!f', byte_array)[0]
    return float_num