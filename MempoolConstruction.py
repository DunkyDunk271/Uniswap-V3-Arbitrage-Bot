class Pools:
    def __init__(self, id, token0TotalSupply, token1TotalSupply, token0ID, token1ID):
        self.id = id
        self.token0TotalSupply = token0TotalSupply
        self.token1TotalSupply = token1TotalSupply
        self.token0ID = token0ID
        self.token1ID = token1ID

class PendingTransaction:
    def __init__(self, hash, nonce, blockHash, blockNumber, transactionIndex, fromAddress, toAddress, value, gasPrice, gas):
        self.hash = hash
        self.nonce = nonce
        self.blockHash = blockHash
        self.blockNumber = blockNumber
        self.transactionIndex = transactionIndex
        self.fromAddress = fromAddress
        self.toAddress = toAddress
        self.value = value  
        self.gasPrice = gasPrice
        self.gas = gas
        