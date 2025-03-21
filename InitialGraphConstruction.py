import MempoolConstruction
import requests
import json
import math
import time
from web3 import Web3
from multicall import Call, Multicall

GRAPHQL_URL = "https://gateway.thegraph.com/api/8eb05dafcde7a82f664adace07cb1437/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
INFURA_RPC = "https://mainnet.infura.io/v3/655599352d27480195e2cf5c52581754"

OUTPUT_FILE = "data/uniswap_v3_reserves.json"

w3 = Web3(Web3.HTTPProvider(INFURA_RPC))

async def process_pools():
    PoolList = []
    start_time = time.time()
    pools = fetch_pools()
    results = []

    calls = []
    for pool in pools:
        pool_id = pool["id"]
        if not pool_id: 
            continue

        call = Call(
            target=pool_id,
            function='slot0()(uint160,int24)',
            returns=[[pool_id, lambda x: x]]
        )
        calls.append(call)

    if not calls:
        print("Error: No valid calls created for Multicall!")
        return []

    #try:
    slot0_results = Multicall(calls, _w3=w3)()

    for pool in pools:
        pool_id = pool["id"]
        fee_tier = float(pool["feeTier"])
        token0_symbol = pool["token0"]["symbol"]
        token0_id = pool["token0"]["id"]
        token1_symbol = pool["token1"]["symbol"]
        token1_id = pool["token1"]["id"]
        token0_decimals = int(pool["token0"]["decimals"])
        token1_decimals = int(pool["token1"]["decimals"])
        positions = []

        if pool_id not in slot0_results:
            continue
        
        print(slot0_results[pool_id])
        sqrtPriceX96, tick = slot0_results[pool_id]

        positions_query = f"""
        {{
        positions(where: {{ pool: "{pool_id}" }}) {{
            id
            liquidity
            tickLower {{
            tickIdx
            }}
            tickUpper {{
            tickIdx
            }}
        }}
        }}
        """
        response = requests.post(GRAPHQL_URL, json={'query': positions_query})
        data = response.json()

        if "data" in data and "positions" in data["data"]:
            for position in data["data"]["positions"]:
                pos = {
                    "tickLower": int(position["tickLower"]["tickIdx"]),
                    "tickUpper": int(position["tickUpper"]["tickIdx"]),
                    "liquidity": int(position["liquidity"]),
                    "token0_reserve": 0,
                    "token1_reserve": 0
                }
                positions.append(pos)

        print(f"Pool: {token0_symbol}/{token1_symbol}")
        newPool = MempoolConstruction.Pool(pool_id, fee_tier, positions, token0_symbol, token0_id, token0_decimals, token1_symbol, token1_id, token1_decimals)
        PoolList.append(newPool)

    #except Exception as e:
        #print(f"Multicall Error: {e}")

    end_time = time.time()
    print(f"Pool Info Query execution time: {end_time - start_time:.2f} seconds")

    # Compute reserves
    start_time = time.time()
    for Pool in PoolList:
        pool_id = Pool.get_pool_id()
        if pool_id not in slot0_results:
            continue

        sqrtPriceX96, tick = slot0_results[pool_id]
        token0_reserve = 0
        token1_reserve = 0

        for position in Pool.get_positions():
            tickLower = int(position["tickLower"])
            tickUpper = int(position["tickUpper"])
            liquidity = int(position["liquidity"])
            x, y = compute_token_reserves(liquidity, sqrtPriceX96, tickLower, tickUpper)
            token0_reserve += x
            token1_reserve += y
            position["token0_reserve"] = x
            position["token1_reserve"] = y

        token0_reserve /= 10 ** token0_decimals
        token1_reserve /= 10 ** token1_decimals

        Pool.token0_reserve = token0_reserve
        Pool.token1_reserve = token1_reserve

        results.append({
            "pool_id": pool_id,
            "token0": token0_symbol,
            "token1": token1_symbol,
            "token0_reserve": token0_reserve,
            "token1_reserve": token1_reserve
        })

        print(f"Pool: {token0_symbol}/{token1_symbol}, Reserves: {token0_reserve} {token0_symbol}, {token1_reserve} {token1_symbol}")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=4)

    end_time = time.time()
    print(f"Websocket info execution time: {end_time - start_time:.2f} seconds")
    print(f"Results saved to {OUTPUT_FILE}")

def fetch_pools():
    query = """
    {
      pools(first: 20, orderBy: volumeUSD, orderDirection: desc) {
        id
        feeTier
        token0 {
          symbol
          id
          decimals
        }
        token1 {
          symbol
          id
          decimals
        }
      }
    }
    """
    response = requests.post(GRAPHQL_URL, json={'query': query})
    data = response.json()
    with open("data/pools_data.json", "w") as f:
        json.dump(data, f, indent=4)
    
    if "data" in data and "pools" in data["data"]:
        return data["data"]["pools"]
    else:
        print("Error fetching pools:", data)
        return []

def compute_token_reserves(liquidity, sqrtPriceX96, tickLower, tickUpper):
    P = (sqrtPriceX96 / (2 ** 96)) ** 2
    P_low = 1.0001 ** tickLower
    P_high = 1.0001 ** tickUpper

    sqrtP = math.sqrt(P)
    sqrtP_low = math.sqrt(P_low)
    sqrtP_high = math.sqrt(P_high)

    if P <= P_low:
        x = liquidity * (sqrtP_high - sqrtP_low) / (sqrtP_low * sqrtP_high)
        y = 0
    elif P >= P_high:
        x = 0
        y = liquidity * (sqrtP_high - sqrtP_low)
    else:
        x = liquidity * (sqrtP_high - sqrtP) / (sqrtP * sqrtP_high)
        y = liquidity * (sqrtP - sqrtP_low)

    return x, y
