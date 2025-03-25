class Pool:
    def __init__(self, id, fee_tier, token0_symbol, token0_id, token0_decimals, token1_symbol, token1_id, token1_decimals, token0_reserve, token1_reserve, tick_spacing, ticks_info):
        self.id = id
        self.fee_tier = fee_tier
        self.token0_symbol = token0_symbol
        self.token0_id = token0_id
        self.token0_reserve = token0_reserve
        self.token1_symbol = token1_symbol
        self.token1_id = token1_id
        self.token1_reserve = token1_reserve
        self.token0_decimals = token0_decimals
        self.token1_decimals = token1_decimals
        self.tick_spacing = tick_spacing
        self.ticks_info = ticks_info
        
        self.fee_rate = (self.fee_tier / 1000000)
        self.estimated_slippage = []
    
    def get_pool_id(self):
        return self.id
    
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
        