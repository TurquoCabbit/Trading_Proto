from time import sleep
import sys
import os

from client import Client

def close_all_position(posi):
    for i in posi['result']:
        if i['is_valid'] and i['data']['size'] > 0:
            client.place_order(i['data']['symbol'], i['data']['side'], i['data']['size'], 0, 0, True)
            sleep(0.1)


if __name__ == '__main__':
    os.system('cls')

    if len(sys.argv) < 3:
        print('Execution cmd :')
        print('Close_all_position.exe <api key> <api secret>')
        print('This script is for test net only!!')
        os.system('pause')
        os._exit(0)

    client = Client('https://api-testnet.bybit.com', api_key = sys.argv[1], api_secret = sys.argv[2])

    position = client.get_all_position()
    close_all_position(position)
            