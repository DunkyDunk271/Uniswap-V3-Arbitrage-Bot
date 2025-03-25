from MempoolConstruction import *
import requests
import json
import websockets
import asyncio
from web3 import Web3

GRAPHQL_URL = "https://gateway.thegraph.com/api/8eb05dafcde7a82f664adace07cb1437/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
QUICKNODE_RPC = "https://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc/"
QUICKNODE_WSS = "wss://yolo-aged-darkness.quiknode.pro/401a21cac95f67e72bb1478cf94b4ff0763535cc"
INFURA_WSS = "wss://mainnet.infura.io/ws/v3/655599352d27480195e2cf5c52581754"
INFURA_RPC = "https://mainnet.infura.io/v3/655599352d27480195e2cf5c52581754"
ALCHEMY_WSS = "wss://eth-mainnet.g.alchemy.com/v2/9qCuMumrhLZzVLIRFV9mELoZ-TlKOFzU"
ALCHEMY_RPC = "https://eth-mainnet.g.alchemy.com/v2/9qCuMumrhLZzVLIRFV9mELoZ-TlKOFzU"
CURRENT_RPC, CURRENT_WSS = ALCHEMY_RPC, ALCHEMY_WSS

UNISWAP_V3_ROUTER = "0xe592427a0aece92de3edee1f18e0157c05861564"
UNISWAP_V2_ROUTER = "0x7a250d5630b4cf539739df2c5dacb4c659f2488d"
PANCAKE_ROUTER = "0x65b382653f7C31bC0Af67f188122035461ec9C76"

def CheckSwapTransaction(data):
    '''
    async with websockets.connect(CURRENT_WSS) as websocket:
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
    '''
            
    if "params" in data and "result" in data["params"]:
        tx_hash = data["params"]["result"]
        tx_details = fetch_transaction_details(tx_hash)
        if tx_details == None:
            return None, None
        toAddress = tx_details['to']
        if toAddress == UNISWAP_V3_ROUTER:
            print("New Uniswap V3 swap:", json.dumps(tx_details, indent=4))
            tx_type = "Uniswap_v3"
            return tx_details, tx_type
        elif toAddress == UNISWAP_V2_ROUTER:
            print("New Uniswap V2 swap:", json.dumps(tx_details, indent=4))
            tx_type = "Uniswap_v2"
            return tx_details, tx_type
        elif toAddress == PANCAKE_ROUTER:
            print("New Pancake swap:", json.dumps(tx_details, indent=4))
            tx_type = "Pancake"
            return tx_details, tx_type
        else:
            return None, None

                    

def fetch_transaction_details(tx_hash):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getTransactionByHash",
        "params": [tx_hash]
    }

    response = requests.post(CURRENT_RPC, json=payload)
    data = response.json()
    
    if "result" in data and data["result"]:
        return data["result"]
    else:
        print("Error fetching transaction details:", data)
        return None
