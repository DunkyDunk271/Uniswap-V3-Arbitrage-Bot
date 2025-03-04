import math
import struct

def GetAmountReceive(token_in, amount_in, Pool):
    #Trade estimation without consideration of gas fee, only consider Uniswap fee
    pass
    

def ReserveEstimation(PendingTransactions, LiquidityPoolIDs, Uni_USDT_Total_Supply, Uni_WETH_Total_Supply, Sushi_USDT_Total_Supply, Sushi_WETH_Total_Supply):
    pass

def ArbitrageOpportunitySpot(Sushi_WETH_Total_Supply, Sushi_USDT_Total_Supply, Uni_WETH_Total_Supply, Uni_USDT_Total_Supply):
    pass

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