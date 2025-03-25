from InitialGraphConstruction import *
from MempoolSniper import *
from PriceCalculation import *
from MempoolConstruction import *
import json
import websockets
import asyncio
from web3 import Web3
import nest_asyncio

nest_asyncio.apply()

GRAPHQL_URL = "https://gateway.thegraph.com/api/8eb05dafcde7a82f664adace07cb1437/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
QUICKNODE_RPC = "https://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc/"
QUICKNODE_WSS = "wss://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc"
INFURA_WSS = "wss://mainnet.infura.io/ws/v3/655599352d27480195e2cf5c52581754"
INFURA_RPC = "https://mainnet.infura.io/v3/655599352d27480195e2cf5c52581754"
ALCHEMY_WSS = "wss://eth-mainnet.g.alchemy.com/v2/9qCuMumrhLZzVLIRFV9mELoZ-TlKOFzU"
ALCHEMY_RPC = "https://eth-mainnet.g.alchemy.com/v2/9qCuMumrhLZzVLIRFV9mELoZ-TlKOFzU"

CURRENT_RPC, CURRENT_WSS = ALCHEMY_RPC, ALCHEMY_WSS
UNISWAP_V3_ROUTER = "0xe592427a0aece92de3edee1f18e0157c05861564"
UNISWAP_V3_POSITIONNFTMANAGER = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
UNISWAP_V2_ROUTER = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"
PANCAKE_ROUTER = "0x65b382653f7C31bC0Af67f188122035461ec9C76"

UNISWAP_V3_ROUTER_ABI = [
    # exactInputSingle: typically used for a single-hop swap.
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct ISwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    # exactInput: for multi-hop swaps (the path is encoded).
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "bytes", "name": "path", "type": "bytes"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"}
                ],
                "internalType": "struct ISwapRouter.ExactInputParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInput",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    # exactOutputSingle: for single-hop swaps targeting an exact output.
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountInMaximum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct ISwapRouter.ExactOutputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactOutputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    # exactOutput: for multi-hop swaps targeting an exact output.
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "bytes", "name": "path", "type": "bytes"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountInMaximum", "type": "uint256"}
                ],
                "internalType": "struct ISwapRouter.ExactOutputParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactOutput",
        "outputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    # multicall: bundles multiple calls in one transaction.
    {
        "inputs": [
            {"internalType": "bytes[]", "name": "data", "type": "bytes[]"}
        ],
        "name": "multicall",
        "outputs": [
            {"internalType": "bytes[]", "name": "results", "type": "bytes[]"}
        ],
        "stateMutability": "payable",
        "type": "function"
    }
]

async def main():
    #PoolList = await process_pools()

    async with websockets.connect(CURRENT_WSS, ping_interval = None, ping_timeout=30) as websocket:
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
            swap_transaction, transaction_type = CheckSwapTransaction(data)
            
            if swap_transaction is None:
                continue

            transaction_input = swap_transaction['input']
            if not transaction_input or transaction_input == "0x":
                return None
            
            if transaction_type == "Uniswap_v3":
                w3 = Web3(Web3.HTTPProvider(CURRENT_RPC))
                contract = w3.eth.contract(address=w3.to_checksum_address(UNISWAP_V3_ROUTER), abi=UNISWAP_V3_ROUTER_ABI)
                
                # Decode the transaction input data.
                func_obj, func_params = contract.decode_function_input(transaction_input)
                fn_name = func_obj.fn_name

                transaction_details = {"function": fn_name, "params": func_params}

                # Determine the transaction type by function name.
                if fn_name == "exactInputSingle":
                    transaction_details["type"] = "Swap (exactInputSingle)"
                elif fn_name == "exactInput":
                    transaction_details["type"] = "Swap (exactInput)"
                elif fn_name == "exactOutputSingle":
                    transaction_details["type"] = "Swap (exactOutputSingle)"
                elif fn_name == "exactOutput":
                    transaction_details["type"] = "Swap (exactOutput)"
                elif fn_name == "multicall":
                    transaction_details["type"] = "Multicall"
                    # Optionally, decode each inner call in the multicall.
                    inner_calls = []
                    inner_data = func_params.get("data")
                    for call_data in inner_data:
                        try:
                            inner_fn_obj, inner_fn_params = contract.decode_function_input(call_data)
                            inner_calls.append({
                                "function": inner_fn_obj.fn_name,
                                "params": inner_fn_params
                            })
                        except Exception as inner_e:
                            inner_calls.append({
                                "error": str(inner_e),
                                "raw_data": call_data
                            })
                    transaction_details["inner_calls"] = inner_calls
                else:
                    transaction_details["type"] = "Unknown"

            
if __name__ == "__main__":
    asyncio.run(main())