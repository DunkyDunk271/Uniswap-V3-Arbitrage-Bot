from InitialGraphConstruction import *
from MempoolSniper import *
from PriceCalculation import *
from MempoolConstruction import *
import json
import websockets
import asyncio
from web3 import Web3

GRAPHQL_URL = "https://gateway.thegraph.com/api/8eb05dafcde7a82f664adace07cb1437/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
QUICKNODE_RPC = "https://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc/"
QUICKNODE_WSS = "wss://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc"
INFURA_WSS = "wss://mainnet.infura.io/ws/v3/655599352d27480195e2cf5c52581754"
INFURA_RPC = "https://mainnet.infura.io/v3/655599352d27480195e2cf5c52581754"

CURRENT_RPC, CURRENT_WSS = INFURA_RPC, INFURA_WSS
UNISWAP_V3_ROUTER = "0xe592427a0aece92de3edee1f18e0157c05861564"
#UNISWAP_V3_ROUTER = "0xb41b78Ce3D1BDEDE48A3d303eD2564F6d1F6fff0"

async def main():
    PoolList = process_pools()

    async with websockets.connect(CURRENT_WSS, ping_interval = 30) as websocket:
        subscribe_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_subscribe",
            "params": ["newPendingTransactions"]
        }

        await websocket.send(json.dumps(subscribe_payload))
        response = await websocket.recv()
        print("Subscription response:", response)
    
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            swap_transaction = CheckSwapTransaction(data)
            
            if swap_transaction == None:
                continue
            


    '''

    LiquidityPoolIDs = [Uni_WETH_ID, Uni_USDT_ID, Sushi_WETH_ID, Sushi_USDT_ID]

    PendingTransactions = ReadMempool()
    
    PendingTransactions = PotentialNextBlock(PendingTransactions)

    PendingTransactions = TransactionFilter(PendingTransactions, LiquidityPoolIDs)

    Sushi_WETH_Total_Supply, Sushi_USDT_Total_Supply, Uni_WETH_Total_Supply, Uni_USDT_Total_Supply = ReserveEstimation(PendingTransactions, LiquidityPoolIDs, Uni_USDT_Total_Supply, Uni_WETH_Total_Supply, Sushi_USDT_Total_Supply, Sushi_WETH_Total_Supply)

    Opportunity = ArbitrageOpportunitySpot(Sushi_WETH_Total_Supply, Sushi_USDT_Total_Supply, Uni_WETH_Total_Supply, Uni_USDT_Total_Supply)
    if Opportunity == "UniWETH-USDT/SushiUSDT-WETH":
        OptimalAmount, Profit = OptimalArbitrageAmount(Uni_WETH_Total_Supply, Uni_USDT_Total_Supply, Uni_USDT_Total_Supply, Uni_WETH_Total_Supply)
    elif Opportunity == "UniUSDT-WETH/SushiWETH-USDT":
        OptimalAmount, Profit = OptimalArbitrageAmount(Uni_USDT_Total_Supply, Uni_WETH_Total_Supply, Sushi_WETH_Total_Supply, Sushi_USDT_Total_Supply)
    else:
        print(Opportunity)
    
    print(f"Optimal Amount: {OptimalAmount}")
    print(f"Profit: {Profit}")
    '''

if __name__ == "__main__":
    asyncio.run(main())