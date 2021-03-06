from pybit import HTTP
from uuid import uuid4
import os
from datetime import datetime

from Make_log import Log
from error_code import get_error_msg

class Client_USDT_Perpetual:
    def __init__(self, endpoint, api_key, api_secret) -> None:
        self.client = HTTP(endpoint = endpoint, api_key = api_key, api_secret = api_secret, request_timeout = 60)
        
        self.pybit_except_ending = '}.'
        self.log = Log('log')
    
    def error_msg_check(self, err):
        if not err.endswith(self.pybit_except_ending):
            raise Exception(err)

    def Error_Msg(self, str = ''):
        self.log.log(str)
        str = str.split('\n')

        for i in str:
            os.system('echo [31m{} : {}'.format(datetime.now().strftime('%H:%M:%S'), i))        
        os.system('echo [0m{} :'.format(datetime.now().strftime('%H:%M:%S')))

    def query_symbol(self, coin = 'USDT'):
        try:
            data = self.client.query_symbol()['result']
            symbol = []
            for i in data:
                if i['quote_currency'] == coin:
                    symbol.append(i)
            del data 
            return symbol

        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Query symbol Fail!!\n#{} : {}\n{}'.format(ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False


    def get_wallet_balance(self, coin = 'USDT'):
        try:
            return self.client.get_wallet_balance(coin = coin)['result'][coin]
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Get wallet balance Fail!!\n#{} : {}\n{}'.format(ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case '10003' | '10005':   # invalid api_key or wrong Permission
                    os.system('pause')
                    os._exit(0)
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def get_all_position(self, endpoint = '/private/linear/position/list'):
        try:
            return self.client.my_position(endpoint = endpoint)
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Query Position Fail!!\n#{} : {}\n{}'.format(ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case '10003' | '10005':   # invalid api_key or wrong Permission 
                    os.system('pause')
                    os._exit(0)
                case _:
                    self.log.log('untrack_error_code')
                    os.system('pause')
                    os._exit(0)

    def get_entry_price(self, symbol, side):
        try:
            rc = self.client.my_position(symbol = symbol)['result']
            if side == 'Buy' and rc[0]['side'] == side and rc[0]['size'] > 0:
                return rc[0]['entry_price']
            elif side == 'Sell' and rc[1]['side'] == side and rc[1]['size'] > 0:
                return rc[1]['entry_price']
            else:
                self.Error_Msg('Get {} position entry price Fail!!\nData not match'.format(symbol))
                return False
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Get {} position entry price Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def get_last_closed_pnl(self, symbol):
        try:
            rc = self.client.closed_profit_and_loss(symbol = symbol, limit = 1, exec_type = 'Trade')['result']['data']
            if len(rc) > 0:
                return rc[0]['closed_pnl']
            else:
                return False
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Get {} closed pnl Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def set_tpsl_mode(self, symbol, mode = 'Full'):
        try:
            self.client.full_partial_position_tp_sl_switch(symbol = symbol, tp_sl_mode = mode)
            return True
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Set {} TPSL mode Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def set_margin_mode(self, symbol, mode, leverage):
        try:
            self.client.cross_isolated_margin_switch(symbol = symbol, is_isolated = mode,
                                                            buy_leverage =leverage, sell_leverage = leverage)
            return True
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Set {} margin mode Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def set_leverage(self, symbol, leverage):
        try:
            self.client.set_leverage(symbol = symbol, buy_leverage = leverage, sell_leverage = leverage)
            return True
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Set {} leverage Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def get_last_price(self, symbol):
        try:
            rc = self.client.latest_information_for_symbol(symbol = symbol)['result']
            if len(rc) > 0:
                return rc[0]
            else:
                return False
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Get {} price Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def place_order(self, symbol, side, qty, TP, SL, close = False):
        try:
            if close == False:
                # open a position
                return self.client.place_active_order(
                                                    symbol = symbol,
                                                    side = side,
                                                    order_type = "Market",
                                                    qty = qty,
                                                    time_in_force = "GoodTillCancel",
                                                    reduce_only = False,
                                                    close_on_trigger = False,
                                                    take_profit = TP,
                                                    stop_loss = SL
                                                )
            elif close == True:
                #close a exist position
                if side == 'Buy':
                    side = 'Sell'
                elif side == 'Sell':
                    side = 'Buy'
                else:
                    raise Exception('fuction parameter error')

                return self.client.place_active_order(
                                                    symbol = symbol,
                                                    side = side,
                                                    order_type = "Market",
                                                    qty = qty,
                                                    time_in_force = "GoodTillCancel",
                                                    reduce_only = True,
                                                    close_on_trigger = False
                                                )


            else:
                raise Exception('fuction parameter error')
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Open {} order Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case '130023':
                    return ret_code
                case '130021':
                    return ret_code
                case _:
                    self.log.log('untrack_error_code')
                    return False
    
    def get_order_status(self, symbol, ID):
        try:
            return self.client.query_active_order(symbol = symbol, order_id = ID)['result']['order_status']
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Get {} lasted opened order Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def set_trailing_stop(self, symbol, side, trailing_stop, TP, SL, trigger):
        try:
            self.client.set_trading_stop(symbol = symbol,
                                         side = side,
                                         trailing_stop = trailing_stop,
                                         take_profit = TP,
                                         stop_loss = SL,
                                         tp_trigger_by = trigger,
                                         sl_trigger_by = trigger)
            return True
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Set {} trailing and fine tune TPSL Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def set_TPSL(self, symbol, side, TP, SL, trigger):
        try:
            self.client.set_trading_stop(symbol = symbol,
                                         side = side,
                                         take_profit = TP,
                                         stop_loss = SL,
                                         tp_trigger_by = trigger,
                                         sl_trigger_by = trigger)
            return True
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('{} fine tune TPSL Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def set_transfer_spot_to_contract(self, amount = 0, coin = 'USDT'):
        if amount == 0:
            return False
        
        try:
            self.client.create_internal_transfer(transfer_id=str(uuid4()),
                                                 coin = coin,
                                                 amount = str(amount),
                                                 from_account_type = 'SPOT',
                                                 to_account_type = 'CONTRACT')
            return True
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Transfer {} {} from SPOT to CONTRACT Fail!!\n#{} : {}\n{}'.format(amount, coin, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case '38001' | '90001':
                    return False
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def set_transfer_contract_to_spot(self, amount = 0, coin = 'USDT'):
        if amount == 0:
            return False
        
        try:
            self.client.create_internal_transfer(transfer_id=str(uuid4()),
                                                 coin = coin,
                                                 amount = str(amount),
                                                 from_account_type = 'CONTRACT',
                                                 to_account_type = 'SPOT')
            return True
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Transfer {} {} from CONTRACT to SPOT Fail!!\n#{} : {}\n{}'.format(amount, coin, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case '38001' | '90001':
                    return False
                case _:
                    self.log.log('untrack_error_code')
                    return False

class Client_Spot:
    def __init__(self, endpoint, api_key, api_secret) -> None:
        self.client = HTTP(endpoint = endpoint, api_key = api_key, api_secret = api_secret, spot=True, request_timeout = 60)
        
        self.pybit_except_ending = '}.'
        self.log = Log('log')
    
    def error_msg_check(self, err):
        if not err.endswith(self.pybit_except_ending):
            raise Exception(err)

    def Error_Msg(self, str = ''):
        self.log.log(str)
        str = str.split('\n')

        for i in str:
            os.system('echo [31m{} : {}'.format(datetime.now().strftime('%H:%M:%S'), i))        
        os.system('echo [0m{} :'.format(datetime.now().strftime('%H:%M:%S')))

    def query_symbol(self, base = False, quote = False):
        try:
            data = self.client.query_symbol()['result']
            if not base and not quote:
                return data
            
            symbol = []
            if not quote:
                for i in data:
                    if i['baseCurrency'] == base:
                        symbol.append(i)
                del data
            elif not base:
                for i in data:
                    if i['quoteCurrency'] == quote:
                        symbol.append(i)
                del data
            else:
                for i in data:
                    if i['quoteCurrency'] == quote and i['baseCurrency'] == base:
                        symbol.append(i)
                del data

            if len(symbol) > 0:
                return symbol
            else:
                return False

        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Query symbol Fail!!\n#{} : {}\n{}'.format(ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def get_wallet_balance(self):
        try:
            data = self.client.get_wallet_balance()['result']['balances']
            balance = {}
            for i in data:
                balance[i['coin']] = {'total' : i['total'], 'free' : i['free'], 'locked' : i['locked']}
            del data
            return balance

        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Get wallet balance Fail!!\n#{} : {}\n{}'.format(ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case '-1022' | '-2014' | '-2015':   # invalid api_key
                    os.system('pause')
                    os._exit(0)
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def get_last_price(self, symbol):
        try:
            return self.client.latest_information_for_symbol(symbol = symbol)['result']['lastPrice']
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Get {} price Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def place_matket_order(self, symbol, side, qty):
        try:
            return self.client.place_active_order(symbol = symbol,
                                                  qty = qty,
                                                  side = side,
                                                  type = 'MARKET',
                                                  time_in_force = 'GTC'
                                                 )
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Open {} order Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False
    
    def place_limit_order(self, symbol, side, qty, price):
        try:
            return self.client.place_active_order(symbol = symbol,
                                                  qty = qty,
                                                  side = side,
                                                  type = 'LIMIT',
                                                  time_in_force = 'GTC',
                                                  price = price
                                                 )
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Open {} order Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False
    
    def get_order_status(self, symbol, ID):
        try:
            return self.client.get_active_order(orderId = ID)['result']['status']
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Get {} lasted opened order Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def cancel_order(self, symbol, ID):
        try:
            status = self.client.cancel_active_order(orderId = ID)['result']['status']
            if status == 'CANCELED':
                return True
            else:
                return status
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Get {} lasted opened order Fail!!\n#{} : {}\n{}'.format(symbol, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def set_transfer_spot_to_contract(self, amount = 0, coin = 'USDT'):
        if amount == 0:
            return False
        
        try:
            self.client.create_internal_transfer(transfer_id=str(uuid4()),
                                                 coin = coin,
                                                 amount = str(amount),
                                                 from_account_type = 'SPOT',
                                                 to_account_type = 'CONTRACT')
            return True
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Transfer {} {} from SPOT to CONTRACT Fail!!\n#{} : {}\n{}'.format(amount, coin, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case '38001' | '90001':
                    return False
                case _:
                    self.log.log('untrack_error_code')
                    return False

    def set_transfer_contract_to_spot(self, amount = 0, coin = 'USDT'):
        if amount == 0:
            return False
        
        try:
            self.client.create_internal_transfer(transfer_id=str(uuid4()),
                                                 coin = coin,
                                                 amount = str(amount),
                                                 from_account_type = 'CONTRACT',
                                                 to_account_type = 'SPOT')
            return True
        except Exception as err:
            err = str(err)
            self.error_msg_check(err)
            ret_code = err.split('(ErrCode: ')[1].split(')')[0]
            ret_note = err.split('(ErrCode: ')[0]
            self.Error_Msg('Transfer {} {} from CONTRACT to SPOT Fail!!\n#{} : {}\n{}'.format(amount, coin, ret_code, get_error_msg(ret_code), ret_note))
            match ret_code:
                case '38001' | '90001':
                    return False
                case _:
                    self.log.log('untrack_error_code')
                    return False