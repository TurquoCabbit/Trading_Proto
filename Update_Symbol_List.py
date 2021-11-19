from pybit import HTTP
import os
import json

from error_code import get_error_msg

Symbol_list_ver = 'A'
Symbol_list = {'version' : Symbol_list_ver, 'name' : [], 'data' : []}

def Error_Msg(str = ''):
    str = str.split('\n')

    for i in str:
        os.system('echo [31m{}'.format(i))        
    os.system('echo [0m')

def Query_USDT_Perpetual_Symbol(testnet = 0):
    
    if testnet:
        client = HTTP('https://api-testnet.bybit.com')
    else :
        client = HTTP('https://api.bybit.com')

    try:
        Symbol = client.query_symbol()
        client._exit()
        del client

    except Exception as err:
        err = str(err)
        ret_code = err.split('(ErrCode: ')[1].split(')')[0]
        ret_note = err.split('(ErrCode: ')[0]
        Error_Msg('Query all symbol Fail!!\n#{} : {}\n{}'.format(ret_code, get_error_msg(ret_code), ret_note))
        match ret_code:
            case _:
                os.system('pause')
                os._exit(0)

    for i in Symbol['result']:
        if i['name'].endswith('USDT'):
            Symbol_list['name'].append(i['name'])
            Symbol_list['data'].append(i)

    with open('Symbol_list.json', 'w') as file:
        json.dump(Symbol_list, file, indent = 4)
        return True

    return False

if __name__ == '__main__':
    Query_USDT_Perpetual_Symbol()

    print('Query all USDT Perpetual Symbol done!!')
    os.system('pause')
    os._exit(0)