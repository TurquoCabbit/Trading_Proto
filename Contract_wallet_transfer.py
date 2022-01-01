import sys
import os
from time import sleep
from math import floor

from client import Client_USDT_Perpetual

if __name__ == '__main__':
    os.system('cls')

    if len(sys.argv) < 4:
        print('Execution cmd :')
        print('Contract_wallet_transfer.exe <api key> <api secret> <amount>')
        print('This script is for test net only!!')
        os.system('pause')
        os._exit(0)
    
    api_key = sys.argv[1]
    api_secret = sys.argv[2]
    amount = float(sys.argv[3])
    amount = floor(amount * 10000) / 10000

    client = Client_USDT_Perpetual('https://api-testnet.bybit.com', api_key = sys.argv[1], api_secret = sys.argv[2])

    #Get avlliable balance
    balance = client.get_wallet_balance()
    if balance == False:
        client.Error_Msg('Get contract wallet Fail!! abort transfer.')
        os._exit(0)

    balance = float(balance['available_balance'])
    balance = floor(balance * 10000) / 10000
    if balance == amount:
        os._exit(0)
    

    if balance > 0:
        if not client.set_transfer_contract_to_spot(balance):
            client.Error_Msg('Transfer {} USDT from contract to spot Fail!!'.format(balance))
            os._exit(0)

    sleep(0.1)
    
    if amount > 0:
        if not client.set_transfer_spot_to_contract(amount):
            client.Error_Msg('Transfer {} USDT from spot to contract Fail!!'.format(amount))
            os._exit(0)
