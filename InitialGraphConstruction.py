from MempoolConstruction import *
import requests
import json
import math
import time

GRAPHQL_URL = "https://gateway.thegraph.com/api/8eb05dafcde7a82f664adace07cb1437/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
QUICKNODE_RPC = "https://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc/"
INFURA_RPC = "https://mainnet.infura.io/v3/655599352d27480195e2cf5c52581754"

CURRENT_RPC = INFURA_RPC
OUTPUT_FILE = "data/uniswap_v3_reserves.json"


def process_pools():
    PoolList = []
    start_time = time.time()
    pools = fetch_pools()
    results = []

    for pool in pools:
        pool_id = pool["id"]
        fee_tier = float(pool["feeTier"])
        token0_symbol = pool["token0"]["symbol"]
        token0_id = pool["token0"]["id"]
        token1_symbol = pool["token1"]["symbol"]
        token1_id = pool["token0"]["id"]
        token0_decimals = int(pool["token0"]["decimals"])
        token1_decimals = int(pool["token1"]["decimals"])
        positions = []

        sqrtPriceX96, tick = fetch_slot0(pool_id)

        if sqrtPriceX96 is None or tick is None:
            continue

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
            token0_reserve = 0
            token1_reserve = 0

            for position in data["data"]["positions"]:
                pos = {}
                liquidity = int(position["liquidity"])
                tickLower = int(position["tickLower"]["tickIdx"])
                tickUpper = int(position["tickUpper"]["tickIdx"])
            
                x, y = compute_token_reserves(liquidity, sqrtPriceX96, tickLower, tickUpper)
                token0_reserve += x
                token1_reserve += y
                pos["tickLower"] = tickLower
                pos["tickUpper"] = tickUpper
                pos["liquidity"] = liquidity
                pos["token0_reserve"] = x
                pos["token1_reserve"] = y
                positions.append(pos)

            token0_reserve /= 10 ** token0_decimals
            token1_reserve /= 10 ** token1_decimals

            results.append({
                "pool_id": pool_id,
                "token0": token0_symbol,
                "token1": token1_symbol,
                "token0_reserve": token0_reserve,
                "token1_reserve": token1_reserve
            })

            print(f"Pool: {token0_symbol}/{token1_symbol}, Reserves: {token0_reserve} {token0_symbol}, {token1_reserve} {token1_symbol}")
        PoolList.append(Pool(pool_id, fee_tier, positions, token0_symbol, token0_id, token0_reserve, token1_symbol, token1_id, token1_reserve))


    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=4)

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")
    print(f"Results saved to {OUTPUT_FILE}")


def fetch_pools():
    query = """
    {
      pools(first: 10, orderBy: volumeUSD, orderDirection: desc) {
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


#def fetch_position(pool_id):


def fetch_slot0(pool_address):
    SLOT0_METHOD_ID = "0x3850c7bd"
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [
            {
                "to": pool_address,
                "data": SLOT0_METHOD_ID
            },
            "latest"
        ]
    }

    response = requests.post(CURRENT_RPC, json=payload)
    data = response.json()

    if "result" in data:
        result = data["result"]
        sqrtPriceX96 = int(result[2:66], 16)
        tick = int(result[66:130], 16)
        return sqrtPriceX96, tick
    else:
        print(f"Error fetching slot0 for pool {pool_address}:", data)
        return None, None


def sqrtPriceX96_to_price(sqrtPriceX96):
    return (sqrtPriceX96 / (2 ** 96)) ** 2


def tick_to_price(tickIdx):
    return 1.0001 ** tickIdx


def compute_token_reserves(liquidity, sqrtPriceX96, tickLower, tickUpper):
    P = sqrtPriceX96_to_price(sqrtPriceX96)
    P_low = tick_to_price(tickLower)
    P_high = tick_to_price(tickUpper)

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


