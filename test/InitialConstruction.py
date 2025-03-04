import requests
import json
import websockets
import asyncio
import time
import math

def Construct_Graph():
    start_time = time.time()
    pools = Initial_Info_Query()
    results = []

    for pool in pools:
        pool_id = pool["id"]
        token0_symbol = pool["token0"]["symbol"]
        token0_id = pool["token0"]["id"]
        token1_symbol = pool["token1"]["symbol"]
        token1_id = pool["token1"]["id"]
        tickLower = pool["tickLower"]["tickIdx"]
        tickUpper = pool["tickUpper"]["tickIdx"]
        liquidity = pool["liquidity"]
        sqrtPriceX96, currentTick = fetch_slot0(pool_id)

        if sqrtPriceX96 is None or currentTick is None:
            continue
        
        positions_query = f"""

def Initial_Info_Query():
  # API Key: 8eb05dafcde7a82f664adace07cb1437
  UNISWAP_V3_URL = "https://gateway.thegraph.com/api/8eb05dafcde7a82f664adace07cb1437/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
  
  # Uniswap V3 Query for 200 pools with largest totalValueLockedUSD
  UNISWAP_QUERY = """
{
  positions(first: 200, orderBy: pool__volumeUSD) {
    id
    liquidity
    tickUpper {
      id
      tickIdx
    }
    tickLower {
      id
      tickIdx
    }
    pool {
      id
      token1 {
        symbol
        id
      }
      token0 {
        symbol
        id
      }
    }
  }
}
  """

  response = requests.post(UNISWAP_V3_URL, json={"query": UNISWAP_QUERY})

  # Check if the request was successful
  if response.status_code == 200:
      data = response.json()
      print("Data successfully fetched")
      return data["data"]["pools"]

  else:
    print(f"Error {response.status_code}: {response.text}")
    return []


def fetch_slot0(pool_address):
    SLOT0_METHOD_ID = "0x3850c7bd"  # Function selector for slot0()
    
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

    response = requests.post(QUICKNODE_RPC, json=payload)
    data = response.json()

    if "result" in data:
        result = data["result"]
        sqrtPriceX96 = int(result[2:66], 16)  # Extract sqrtPriceX96
        tick = int(result[66:130], 16)  # Extract tick
        return sqrtPriceX96, tick
    else:
        print(f"Error fetching slot0 for pool {pool_address}:", data)
        return None, None


def Pool_Balance_Info_Query():
  QUICKNODE_RPC = "https://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc/"  
  POOL_ADDRESS = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8" 
  SLOT0_METHOD_ID = "0x3850c7bd"

  payload = {
      "jsonrpc": "2.0",
      "id": 1,
      "method": "eth_call",
      "params": [
          {
              "to": POOL_ADDRESS,
              "data": SLOT0_METHOD_ID
          },
          "latest"
      ]
  }

  response = requests.post(QUICKNODE_RPC, json=payload)
  data = response.json()

  if 'result' in data:
      result = data['result']
      sqrtPriceX96 = int(result[2:66], 16)  # Extract sqrtPriceX96
      tick = int(result[66:130], 16)  # Extract tick
      print(result)
      #print(f"sqrtPriceX96: {sqrtPriceX96}")
      #print(f"Tick: {tick}")
  else:
      print("Error fetching liquidity data:", data)


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

    if P <= P_low:  # All in token0
        x = liquidity * (sqrtP_high - sqrtP_low) / (sqrtP_low * sqrtP_high)
        y = 0
    elif P >= P_high:  # All in token1
        x = 0
        y = liquidity * (sqrtP_high - sqrtP_low)
    else:  # Active liquidity in range
        x = liquidity * (sqrtP_high - sqrtP) / (sqrtP * sqrtP_high)
        y = liquidity * (sqrtP - sqrtP_low)

    return x, y