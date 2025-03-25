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

# ABI
pool_abi = [
  {
    "inputs": [],
    "name": "slot0",
    "outputs": [
      {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
      {"internalType": "int24", "name": "tick", "type": "int24"},
      {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
      {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
      {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
      {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
      {"internalType": "bool", "name": "unlocked", "type": "bool"}
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "tickSpacing",
    "outputs": [
      {"internalType": "int24", "name": "", "type": "int24"}
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {"internalType": "int24", "name": "", "type": "int24"}
    ],
    "name": "ticks",
    "outputs": [
      {"internalType": "uint128", "name": "liquidityGross", "type": "uint128"},
      {"internalType": "int128", "name": "liquidityNet", "type": "int128"},
      {"internalType": "uint256", "name": "feeGrowthOutside0X128", "type": "uint256"},
      {"internalType": "uint256", "name": "feeGrowthOutside1X128", "type": "uint256"},
      {"internalType": "int56", "name": "tickCumulativeOutside", "type": "int56"},
      {"internalType": "uint160", "name": "secondsPerLiquidityOutsideX128", "type": "uint160"},
      {"internalType": "uint32", "name": "secondsOutside", "type": "uint32"},
      {"internalType": "bool", "name": "initialized", "type": "bool"}
    ],
    "stateMutability": "view",
    "type": "function"
  }
]

async def process_pools():
    PoolList = []
    start_time = time.time()
    pools = fetch_pools()
    results = []

    if not w3.is_connected(True):
        raise Exception("Không kết nối được tới Ethereum node!")

    for pool in pools:
        pool_id = pool["id"]
        fee_tier = float(pool["feeTier"])
        token0_symbol = pool["token0"]["symbol"]
        token0_id = pool["token0"]["id"]
        token0_reserve = 0
        token0_decimals = int(pool["token0"]["decimals"])
        token1_symbol = pool["token1"]["symbol"]
        token1_id = pool["token1"]["id"]
        token1_reserve = 0
        token1_decimals = int(pool["token1"]["decimals"])
        ticks_info = {}
        pool_address = w3.to_checksum_address(pool_id)

        pool_contract = w3.eth.contract(address=pool_address, abi=pool_abi)
        try:
            slot0 = pool_contract.functions.slot0().call()
            if not slot0:
                raise Exception("Error fetching slot0")
        except Exception as e:
            print(f"Error fetching slot0: {e}")

        sqrtPriceX96 = slot0[0]
        current_tick = slot0[1]
        
        tick_spacing = pool_contract.functions.tickSpacing().call()
        nearest_tick = (current_tick // tick_spacing) * tick_spacing

        range_steps = 50
        tick_indexes = [nearest_tick + i * tick_spacing for i in range(-range_steps, range_steps + 1)]

        calls = []
        for tick_idx in tick_indexes:
            # (liquidityGross, liquidityNet, feeGrowthOutside0X128, feeGrowthOutside1X128, tickCumulativeOutside, secondsPerLiquidityOutsideX128, secondsOutside, initialized)
            call = Call(
                pool_address,
                ['ticks(int24)(uint128,int128,uint256,uint256,int56,uint160,uint32,bool)', tick_idx],
                [(str(tick_idx), lambda x: x)]
            )
            calls.append(call)

        tick_results = Multicall(calls, _w3=w3)()
        for tick_key in sorted(tick_results.keys(), key=lambda x: int(x)):
            data = tick_results[tick_key]
            if data is None:
                print(f"Tick {tick_key}: None")
                continue

            # Get liquidityGross
            liquidityGross = data
            # Calculate Pa, Pb
            # Pa = 1.0001^(tick), Pb = 1.0001^(tick + tickSpacing)
            tick_i = int(tick_key)
            Pa = tick_to_price(tick_i)
            Pb = tick_to_price(tick_i + tick_spacing)
            sqrt_pa = math.sqrt(Pa)
            sqrt_pb = math.sqrt(Pb)
            
            # Estimate token0_amount, token1_amount
            token0_reserve_tick = 0
            token1_reserve_tick = 0
            if sqrt_pa > 0 and sqrt_pb > 0:
                token0_reserve_tick = liquidityGross * (sqrt_pb - sqrt_pa) / (sqrt_pb * sqrt_pa)
                token1_reserve_tick = liquidityGross * (sqrt_pb - sqrt_pa)
                token0_reserve += token0_reserve_tick
                token1_reserve += token1_reserve_tick
            ticks_info[tick_i] = {
                "liquidityGross": liquidityGross,
                "Pa": Pa,
                "Pb": Pb,
                "token0_reserve": token0_reserve_tick,
                "token1_reserve": token1_reserve_tick
            }
              

        print(f"Pool: {token0_symbol}/{token1_symbol}, Reserve: {token0_reserve} {token0_symbol}, {token1_reserve} {token1_symbol}")
        newPool = MempoolConstruction.Pool(pool_id, fee_tier, token0_symbol, token0_id, token0_decimals, token1_symbol, token1_id, token1_decimals, token0_reserve, token1_reserve, tick_spacing, ticks_info)
        PoolList.append(newPool)

        results.append({
          "pool_id": pool_id,
          "token0": token0_symbol,
          "token1": token1_symbol,
          "token0_reserve": token0_reserve,
          "token1_reserve": token1_reserve
        })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=4)

    end_time = time.time()
    print(f"Websocket info execution time: {end_time - start_time:.2f} seconds")
    print(f"Results saved to {OUTPUT_FILE}")
    '''
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
            positions.append(pos)'

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
  '''


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

def tick_to_price(tick: int) -> float:
    return 1.0001 ** tick

def sqrtPriceX96_to_tick(sqrtPriceX96: int) -> int:
    q = 2 ** 96
    return int(2 * math.log(sqrtPriceX96 / q) / math.log(1.0001))