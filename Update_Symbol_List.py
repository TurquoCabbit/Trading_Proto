from pybit import HTTP
import os
import json

import Make_log

Symbol_list_ver = 'A'
Symbol_list = {'version' : Symbol_list_ver, 'name' : [], 'data' : []}

def Error_Msg(str, extreme = 0):
    log.log(str)
    if extreme:
        os.system('echo [41m{}'.format(str))
        os.system('echo [0m{}'.format('--------------------------------------------------------------------'))
    else:
        os.system('echo [31m{}'.format(str))
        os.system('echo [0m{}'.format('--------------------------------------------------------------------'))

def Querry_USDT_Perpetual_Symbol(testnet = 0):
    
    try:
        if testnet:
            client = HTTP('https://api-testnet.bybit.com')
        else :
            client = HTTP('https://api.bybit.com')
    except:
        Error_Msg('Connect Error')
        return False

    try:
        Symbol_mainnet = client.query_symbol()
        client._exit()
        del client
        if Symbol_mainnet['ret_code']:
            raise Exception('Querry Symbol Error\tReturn code: {}\tReturn msg: {}'.format(Symbol_mainnet['ret_code'], Symbol_mainnet['ret_msg']))
    except Exception as Err:
        Error_Msg(Err)
        return False

    for i in Symbol_mainnet['result']:
        if i['name'].endswith('USDT'):
            Symbol_list['name'].append(i['name'])
            Symbol_list['data'].append(i)

    with open('Symbol_list.json', 'w') as file:
        json.dump(Symbol_list, file, indent = 4)
        return True

    return False

if __name__ == '__main__':
    ### init log
    log = Make_log.Log('')
    log.log_and_show('========================START=========================')

    Querry_USDT_Perpetual_Symbol()

    log.show('Querry all USDT Perpetual Symbol done!!')
    os.system('pause')
    os._exit(0)