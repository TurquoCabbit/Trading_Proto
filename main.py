from time import localtime
from time import strftime
from time import time
from datetime import datetime
import sys
import os
import json
from gc import collect
import random
import csv

from Make_log import Log
import Update_Symbol_List
import Loading_animation
from client import Client

##########################################################
Version = '4.999'
Date = '2021/11/21'

Start_time = (int)(time())

Symbol_List = []

delay = Loading_animation.delay_anima()

Pause_place_order = False

##############################################################################################################################
### init log
log = Log('log')
log.log('\n=============================START==============================')
log.log_and_show('Bybit USDT perpetual trading bot ver {} {}'.format(Version, Date))

class Symbol:
    def __init__(self, Symbol, tick_size, qty_step) -> None:
        self.symbol = Symbol
        self.tick_size = (float)(tick_size)
        self.qty_step = (float)(qty_step)
        self.opened = False
        self.isolate = False
        self.leverage = 0
        self.tpsl_mode = 'Partial'

class Open:
    def __init__(self) -> None:
        self.num = 0
        self.sym = ''
        self.price = 0
        self.side = ''
        self.qty = 0
        self.TP = 0
        self.SL = 0
        self.trailing = 0
        self.order_id = ''

class PNL_data:
    def __init__(self, dir) -> None:
        if not os.path.isdir(dir):
            os.mkdir(dir)
        
        self.start_track_pnl = False
        self.closed_position = 0
        self.win_position = 0
        self.win_rate = 0
        self.total_pnl = 0
        self.total_pnl_rate = 0
        self.track_list = []
        
        self.start_balance = 'start'
        self.current_balance = 0

        self.log = Log('{}/log'.format(dir))

        self.dir = dir

    def load(self):
        if not os.path.isfile('{}/pnl.json'.format(self.dir)):
            return

        with open('{}/pnl.json'.format(self.dir), 'r') as file:
            self.temp = json.load(file)
        try:
            self.closed_position = self.temp['closed_position']
            self.win_position = self.temp['win_position']
            self.win_rate = self.temp['win_rate']
            self.total_pnl = self.temp['total_pnl']
            self.total_pnl_rate = self.temp['total_pnl_rate']
            self.start_balance = self.temp['start_balance']
            self.current_balance = self.temp['current_balance']
        except KeyError:
            self.closed_position = 0
            self.win_position = 0
            self.win_rate = 0
            self.total_pnl = 0
            self.total_pnl_rate = 0            
            self.start_balance = 'start'
            self.current_balance = 0

        del self.temp        
        
    def write(self):
        self.temp = {
            'closed_position' :  self.closed_position,
            'win_position' :  self.win_position,
            'win_rate' :  self.win_rate,
            'total_pnl' :  self.total_pnl,
            'total_pnl_rate' :  self.total_pnl_rate,
            'start_balance' :  self.start_balance,
            'current_balance' :  self.current_balance
        }
        
        with open('{}/pnl.json'.format(self.dir), 'w') as file:
            self.temp = json.dump(self.temp, file, indent = 4)

        del self.temp

    
    def record_balance(self):
        if not os.path.isfile('{}/balance.csv'.format(self.dir)):
            with open('{}/balance.csv'.format(self.dir), 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['time', 'balance'])
        
        with open('{}/balance.csv'.format(self.dir), 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([(int)(time()), self.current_balance])
                

class CFG:
    def __init__(self, version) -> None:
        self.version = version
        self.Test_net = True
        self.Max_operate_position = None
        self.operate_USDT = None
        self.stop_operate_USDT = None
        self.Leverage = None
        self.side = None
        self.TP_percentage = None
        self.SL_percentage = None
        self.Trigger = None
        self.Trailing_Stop = None
        self.Group = None
        self.open_order_interval = None
        self.poll_order_interval = None
        self.Token_list = []
        self.Black_list = []
        
        self.cfg_init = {
                            'Version' : Version,
                            'Run_on_testnet' : True,
                            'Operate_position' : 5,
                            'Order_value_USDT' : 10,
                            'Stop_operate_USDT' : 10,
                            'Leverage' : 20,
                            'Side' : 'Both',
                            'TP_percentage' : 100,
                            'SL_percentage' : 10,
                            'Trigger' : 'LastPrice',
                            'Trailing_Stop_percentag' : 0,
                            'Favorite_group' : 'all',
                            'open_interval' : 1,
                            'poll_interval' : 60,
                            'Black_list' : [],
                            'Group_0' : [
                                'BTC',  'ETH',  'DOT',  'SOL',
                                'BNB',  'FTT',  'UNI',  'AXS',
                                'LUNA', 'ATOM', 'AAVE', 'FTM',
                                'BIT',  'ADA',  'ICP'
                                ]
                        }
    
    def new_cfg(self):
        with open('cfg.json', 'w') as file:
            json.dump(self.cfg_init, file, indent = 4)

    def load_cfg(self):
        with open('cfg.json', 'r') as file:
            self.cfg = json.load(file)
        try:
            self.version = self.cfg['Version']
            if self.version != Version:
                return False
                
            self.Test_net = self.cfg['Run_on_testnet']
            self.Max_operate_position = self.cfg['Operate_position']
            self.operate_USDT = self.cfg['Order_value_USDT']
            self.stop_operate_USDT = self.cfg['Stop_operate_USDT']
            self.Leverage = self.cfg['Leverage']
            self.side = self.cfg['Side']
            self.TP_percentage = self.cfg['TP_percentage']
            self.SL_percentage = self.cfg['SL_percentage']
            self.Trigger = self.cfg['Trigger']
            self.Trailing_Stop = self.cfg['Trailing_Stop_percentag']

            self.Group = self.cfg['Favorite_group']
            self.open_order_interval = self.cfg['open_interval']
            self.poll_order_interval = self.cfg['poll_interval']
            self.Black_list.clear()
            for i in self.cfg['Black_list']:
                self.Black_list.append('{}USDT'.format(i))

            self.Token_list.clear()
            if self.Group in self.cfg and self.Group != 'Black_list':
                for i in self.cfg[self.Group]:
                    self.Token_list.append('{}USDT'.format(i))
            else:
                self.Group = 'all'
            return True
        
        except KeyError:
            self.archive_cfg('cfg.json corrupted, old one archive as cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))
    
    def update_version(self):
        self.version = Version
        self.cfg['Version'] = self.version
        with open('cfg.json', 'w') as file:
            json.dump(self.cfg, file, indent = 4)
    
    def upgrade_cfg(self):
        System_Msg('cfg.json upgraded, old one archive as cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))
        if not os.path.isdir('archive'):
            os.mkdir('archive')
        os.rename('cfg.json', 'archive/cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))

        for i in self.cfg_init:
            if not i in self.cfg:
                self.cfg[i] = self.cfg_init[i]

        self.update_version()

    def archive_cfg(self, msg):
        System_Msg(msg)
        if not os.path.isdir('archive'):
            os.mkdir('archive')
        os.rename('cfg.json', 'archive/cfg_{}.json'.format(strftime('%Y%m%d-%H;%M;%S', localtime(os.path.getmtime('cfg.json')))))
        self.new_cfg()
        log.log_and_show('Generate new cfg.json')
        os.system('pause')
        os._exit(0)

def Error_Msg(str = ''):
    log.log(str)
    str = str.split('\n')

    for i in str:
        os.system('echo [31m{} : {}'.format(datetime.now().strftime('%H:%M:%S'), i))        
    os.system('echo [0m{} :'.format(datetime.now().strftime('%H:%M:%S')))

def System_Msg(str = ''):
    log.log(str)
    str = str.split('\n')

    for i in str:
        os.system('echo [33m{} : {}'.format(datetime.now().strftime('%H:%M:%S'), i))
    os.system('echo [0m{} :'.format(datetime.now().strftime('%H:%M:%S')))

def Print_and_pause(str = ''):
    print(str)
    os.system('pause')

def rand_symbol():
    rand = random.randint(0, len(Symbol_List) - 1)
    if Symbol_List[rand].opened:
        return rand_symbol()
    else:
        return rand
        
def rand_side():
    if random.randint(0, 1):
        return "Buy"
    else:
        return "Sell"
        
def qty_trim(qty, step):
    digi = abs((int)(format(step, '1E').split('E')[1]))
    qty = (int)(qty * pow(10, digi))
    step = (int)(step * pow(10, digi))
    qty -= qty % step    
    return qty / pow(10, digi)

def price_trim(price, tick):
    digi = abs((int)(format(tick, '1E').split('E')[1]))
    price = (int)(price * pow(10, digi))
    tick = (int)(tick * pow(10, digi))
    
    price -= price % tick    
    return price / pow(10, digi)

if __name__ == '__main__':
    ##############################################################################################################################
    ### Load Cfg File
    cfg = CFG(Version)

    if not os.path.isfile('cfg.json'):
        System_Msg('cfg.json file missing. Generate a new one')
        cfg.new_cfg()
        os.system('pause')

    if not cfg.load_cfg():
        if (int)(cfg.version.split('.')[0]) != (int)(Version.split('.')[0]):
            # Main version different
            cfg.upgrade_cfg()
            log.show('Upgrade cfg.json, please check new config or press any key to continue')
            os.system('pause')
            cfg.load_cfg()

        elif (int)(cfg.version.split('.')[1]) < (int)(Version.split('.')[1]):
            #Sub version different
            cfg.update_version()
            cfg.load_cfg()

    ### Check parameter
    if cfg.stop_operate_USDT < cfg.operate_USDT:
        cfg.stop_operate_USDT = cfg.operate_USDT

    if cfg.open_order_interval < 1:
        cfg.open_order_interval = 1
        
    if cfg.poll_order_interval < 10:
        cfg.poll_order_interval = 10

    if cfg.side != 'Buy' and cfg.side != 'Sell':
        cfg.side = 'Both'

    if cfg.Trigger != 'MarkPrice' and cfg.Trigger != 'LastPrice' and cfg.Trigger != 'IndexPrice':
        cfg.Trigger = 'LastPrice'

    log.show('')
    log.log('cfg.json loaded')
    log.log('\tVersion: {}\n\tRun on test net: {}\n\tOperate position: {}\n\tOperate USDT: {}\n'.format(cfg.version, cfg.Test_net, cfg.Max_operate_position, cfg.operate_USDT) +\
            '\tStop_operate_USDT: {}\n\tLeverage: {}\n\tOperate side: {}\n'.format(cfg.stop_operate_USDT, cfg.Leverage, cfg.side) +\
            '\tTP: {}%\n\tSL: {}%\n\tTPSL trigger: {}\n\tTrailing stop: {}%\n'.format(cfg.TP_percentage, cfg.SL_percentage, cfg.Trigger, cfg.Trailing_Stop) +\
            '\tOperate group: {}\n\tOpen order interval: {}s\n\tPolling interval: {}s'.format(cfg.Group, cfg.open_order_interval, cfg.poll_order_interval))

    ##############################################################################################################################
    ### Load history pnl data and init log
    pnl = PNL_data('pnl')

    pnl.log.log('\n=============================START==============================')
    pnl.log.log('Bybit USDT perpetual trading bot ver {} {}'.format(Version, Date))

    pnl.load()

    if pnl.start_balance != 'start':
        pnl.log.log('Start wallet balance: {}\n'.format(pnl.start_balance))

    ##############################################################################################################################
    ### Load Symbol List
    if not os.path.isfile('Symbol_list.json'):
        if Update_Symbol_List.Query_USDT_Perpetual_Symbol():
            with open('Symbol_list.json', 'r') as file:
                Symbol_query = json.load(file)
    else:    
        with open('Symbol_list.json', 'r') as file:
            Symbol_query = json.load(file)

        if Symbol_query['version'] != Update_Symbol_List.Symbol_list_ver:
            if Update_Symbol_List.Query_USDT_Perpetual_Symbol():
                with open('Symbol_list.json', 'r') as file:
                    Symbol_query = json.load(file)

    ##############################################################################################################################
    ### Create client
    if len(sys.argv) == 3:
        if cfg.Test_net:
            # main net api and serect were passed
            log.log('Run on Test Net !!!')
            client = Client('https://api-testnet.bybit.com', api_key=sys.argv[1], api_secret=sys.argv[2])
        else:
            # main net api and serect were passed
            log.log('Run on Main Net !!!')
            client = Client('https://api.bybit.com', api_key=sys.argv[1], api_secret=sys.argv[2])
    else:
        log.show('Execution cmd :')
        log.show('main.exe <api key> <api secret>')
        os.system('pause')
        os._exit(0)

    ### Check Sym list
    if cfg.Group == 'all':
        for i in Symbol_query['data']:
            if not i['name'] in cfg.Black_list:
                Symbol_List.append(Symbol(i['name'], i['price_filter']['tick_size'], i['lot_size_filter']['qty_step']))
    else:
        for i in cfg.Token_list:
            if i in Symbol_query['name'] and not i in cfg.Black_list:
                sym = Symbol_query['data'][Symbol_query['name'].index(i)]
                Symbol_List.append(Symbol(sym['name'], sym['price_filter']['tick_size'], sym['lot_size_filter']['qty_step']))
    
    del Symbol_query

    while True:
        try:
            log.log_and_show(log.get_run_time(Start_time))

            ### Check if eligible symbol qty exceed max operated qty
            if cfg.Max_operate_position > len(Symbol_List):
                System_Msg('Operate_position exceed symbol white list qty\nDecrease Operate_position form {} to {}'\
                           .format(cfg.Max_operate_position, len(Symbol_List)))
                cfg.Max_operate_position = len(Symbol_List)

            ### Query current wallet balance
            wallet = client.get_wallet_balance()
            if wallet != False:
                wallet_available = wallet['available_balance']
                wallet_equity = wallet['equity']
                wallet_real_pnl = wallet['realised_pnl']
                wallet_cum_pnl = wallet['cum_realised_pnl']

                if pnl.start_balance == 'start':
                    pnl.start_balance = wallet_equity
                    pnl.log.log('Start wallet balance: {}\n'.format(pnl.start_balance))
                pnl.current_balance = wallet_equity
                pnl.total_pnl = pnl.current_balance - pnl.start_balance
                if pnl.start_balance != 0:
                    pnl.total_pnl_rate = pnl.total_pnl * 100 / pnl.start_balance
                else:
                    pnl.total_pnl_rate = 0

                pnl.log.log('Current wallet balance:\t{: .2f}\t USDT\n'.format(pnl.current_balance) +\
                            'Unrealized pnl:\t\t\t{: .2f}\tUSDT,\t{: .2f}%\n'.format( pnl.total_pnl, pnl.total_pnl_rate) +\
                            'Daily realized pnl:\t\t{: .2f}\tUSDT\nTotal realized pnl:\t\t{: .2f}\tUSDT\n'.format(wallet_real_pnl, wallet_cum_pnl) +\
                            'Win rate:\t{: .2f}%'.format(pnl.win_rate))
                pnl.write()
                pnl.record_balance()

                log.log_and_show('Balance available:\t{: .2f}\tUSDT\nBalance equity:\t{: .2f}\tUSDT\n'.format(wallet_available, wallet_equity) +\
                                'Unrealized pnl:\t{: .2f}\tUSDT, {: .2f}%\nWin rate: {: .2f}%'.format(pnl.total_pnl, pnl.total_pnl_rate, pnl.win_rate))
                log.show('')

                if wallet_available < cfg.stop_operate_USDT:
                    Pause_place_order = True
                else:
                    Pause_place_order = False

            del wallet

            ### Query current position
            current_position_qty = 0
            current_position_buy = 0
            current_position_sel = 0
            Position_List = {'symbol' : [], 'Buy' : [], 'Sell' : []}
            opened_position = []
            
            position = client.get_all_position()
            
            for i in position['result']:
                if i['is_valid']:
                    if len(Position_List['symbol']) == 0 or Position_List['symbol'][-1] != i['data']['symbol']:
                        Position_List['symbol'].append(i['data']['symbol'])
                        Position_List['Buy'].append(i['data'])
                    else:
                        Position_List['Sell'].append(i['data'])
                else:
                    Error_Msg('{} position data NOT valid'.format(i['data']['symbol']))
            
            ### Chek position status
            for i in Symbol_List:
                if i.symbol in Position_List['symbol']:
                    index = Position_List['symbol'].index(i.symbol)
                    
                    if Position_List['Buy'][index]['is_isolated'] and Position_List['Sell'][index]['is_isolated']:
                        i.isolate = True
                    else:
                        i.isolate = False
                    
                    if Position_List['Buy'][index]['leverage'] == cfg.Leverage and Position_List['Sell'][index]['leverage'] == cfg.Leverage:
                        i.leverage = cfg.Leverage
                    else:
                        i.leverage = 0

                    if Position_List['Buy'][index]['tp_sl_mode'] == 'Full' and Position_List['Sell'][index]['tp_sl_mode'] == 'Full':
                        i.tpsl_mode = 'Full'
                    else:
                        i.tpsl_mode = 'Partial'
                    
                    if Position_List['Buy'][index]['size'] + Position_List['Sell'][index]['size'] > 0:
                        current_position_qty += 1
                        if Position_List['Buy'][index]['position_value'] > 0:
                            current_position_buy += 1
                            opened_position.append({'symbol' : Position_List['symbol'][index], 'side' : 'Buy'})
                        elif Position_List['Sell'][index]['position_value'] > 0:
                            current_position_sel += 1
                            opened_position.append({'symbol' : Position_List['symbol'][index], 'side' : 'Sell'})
                        i.opened = True
                    else:
                        i.opened = False

            ### track opened position
            if len(pnl.track_list) == 0 and len(opened_position) != 0:
                pnl.track_list = opened_position
                if len(opened_position) >= cfg.Max_operate_position:
                    pnl.start_track_pnl = True

            if pnl.start_track_pnl:
                for i in pnl.track_list:
                    if not i in opened_position:
                        closed_pnl = client.get_last_closed_pnl(i['symbol'])
                        if closed_pnl != False:
                            pnl.closed_position += 1
                            if closed_pnl > 0:
                                pnl.win_position += 1
                            
                            pnl.win_rate = pnl.win_position * 100 / pnl.closed_position

                            pnl.log.log('{} {} position was cloasd, pnl : {} USDT'.format(i['symbol'], i['side'], closed_pnl))
                            pnl.write()
                            pnl.track_list.pop(pnl.track_list.index(i))
            
            log.log_and_show('Opened Position: {}\tBuy: {} Sell: {}'.format(current_position_qty, current_position_buy, current_position_sel))
            
            for i in opened_position:
                log.show('\t {}\t{}'.format(i['symbol'], i['side']))
            log.show('')
            
            del opened_position
            del position
            del Position_List
            
            ### Randonly open position
            if not Pause_place_order and current_position_qty < cfg.Max_operate_position:
                random.seed()
                order = Open()

                # Random pick
                order.num = rand_symbol()
                order.sym = Symbol_List[order.num].symbol
                if cfg.side == 'Both':
                    order.side = rand_side()
                else:
                    order.side = cfg.side

                # Set Full Position TP/SL
                if Symbol_List[order.num].tpsl_mode != 'Full':
                    if client.set_tpsl_mode(order.sym) == True:
                        Symbol_List[order.num].tpsl_mode = 'Full'
                    else:
                        Symbol_List.pop(order.num)
                        System_Msg('Remove {} from Symbol List'. format(order.sym))
                        del order
                        collect()
                        delay.delay(cfg.open_order_interval)
                        continue

                # Switch to isolated margin mode and set leverage
                if Symbol_List[order.num].isolate != True:
                    if client.set_margin_mode(order.sym, True, cfg.Leverage) == True:
                        Symbol_List[order.num].isolate = True
                        Symbol_List[order.num].leverage = cfg.Leverage
                    else:
                        Symbol_List.pop(order.num)
                        System_Msg('Remove {} from Symbol List'. format(order.sym))
                        del order
                        collect()
                        delay.delay(cfg.open_order_interval)
                        continue

                # Modify leverage
                if Symbol_List[order.num].leverage != cfg.Leverage:
                    if client.set_leverage(order.sym, cfg.Leverage) == True:
                        Symbol_List[order.num].leverage = cfg.Leverage
                    else:
                        Symbol_List.pop(order.num)
                        System_Msg('Remove {} from Symbol List'. format(order.sym))
                        del order
                        collect()
                        delay.delay(cfg.open_order_interval)
                        continue

                # Query price
                order.price = client.get_last_price(order.sym)
                if order.price == False:
                    Symbol_List.pop(order.num)
                    System_Msg('Remove {} from Symbol List'. format(order.sym))
                    del order
                    collect()
                    delay.delay(cfg.open_order_interval)
                    continue

                # Calculate rough TP/SL and qty
                order.qty = qty_trim((cfg.operate_USDT * cfg.Leverage / order.price), Symbol_List[order.num].qty_step)
                if order.side == 'Buy':
                    order.TP = price_trim((1 + (cfg.TP_percentage / cfg.Leverage / 100)) * order.price, Symbol_List[order.num].tick_size)
                    order.SL = price_trim((1 - (cfg.SL_percentage / cfg.Leverage / 100)) * order.price, Symbol_List[order.num].tick_size)
                elif order.side == 'Sell':
                    order.TP = price_trim((1 - (cfg.TP_percentage / cfg.Leverage / 100)) * order.price, Symbol_List[order.num].tick_size)
                    order.SL = price_trim((1 + (cfg.SL_percentage / cfg.Leverage / 100)) * order.price, Symbol_List[order.num].tick_size)
                
                log.log_and_show('Opening {} {} {} order at about {}'.format(order.qty, order.sym, order.side, order.price))

                # Open order
                place_order = client.place_order(order.sym, order.side, order.qty, order.TP, order.SL)
                if place_order == False or place_order == '130023':
                    Symbol_List.pop(order.num)
                    System_Msg('Remove {} from Symbol List'. format(order.sym))
                    del order
                    collect()
                    delay.delay(cfg.open_order_interval)
                    continue
                elif place_order == '130021':
                    # Stop open order
                    Pause_place_order = True
                    del order
                    collect()
                    delay.delay(cfg.open_order_interval)
                    continue
                else:
                    if place_order['ret_msg'] != 'OK':
                        System_Msg('{} Order Create Successfully !!\nwith return msg: {}'.format(order.sym,temp['ret_msg']))
                    else:
                        log.log_and_show('{} Order Create Successfully !!'.format(order.sym))

                    order.order_id = place_order['result']['order_id']
                    pnl.track_list.append({'symbol' : order.sym, 'side' : order.side})
                    del place_order

                # Get newly placed order status
                retry = 10
                while retry:
                    order_status = client.get_order_status(order.sym, order.order_id)
                    if order_status != False:
                        match order_status:
                            case 'Filled':
                                break
                            case 'Rejected' | 'Cancelled':
                                retry = 0
                                break
                            case _:
                                pass

                        retry -= 1
                        del order_status
                        delay.delay(0.2)
                    else:
                        break

                if retry == 0:
                    # retry fail or error
                    Error_Msg('Query {} lasted order Fail!!'.format(order.sym))
                    del order
                    collect()
                    delay.delay(cfg.open_order_interval)
                    continue

                #Get entry price and Calculate new TP/SL
                order.price = client.get_entry_price(order.sym, order.side)
                if order.price != False:
                    if order.side == 'Buy':
                        order.TP = price_trim((1 + (cfg.TP_percentage / cfg.Leverage / 100)) * order.price, Symbol_List[order.num].tick_size)
                        order.SL = price_trim((1 - (cfg.SL_percentage / cfg.Leverage / 100)) * order.price, Symbol_List[order.num].tick_size)
                    elif order.side == 'Sell':
                        order.TP = price_trim((1 - (cfg.TP_percentage / cfg.Leverage / 100)) * order.price, Symbol_List[order.num].tick_size)
                        order.SL = price_trim((1 + (cfg.SL_percentage / cfg.Leverage / 100)) * order.price, Symbol_List[order.num].tick_size)
                else:
                    del order
                    collect()
                    delay.delay(cfg.open_order_interval)
                    continue
                
                # Calculate and set Trailing stop
                if cfg.Trailing_Stop != 0:
                    order.trailing = price_trim(order.price * (cfg.Trailing_Stop / cfg.Leverage / 100), Symbol_List[order.num].tick_size)

                    # Set trailing stop
                    if client.set_trailing_stop(order.sym, order.side, order.trailing, order.TP, order.SL, cfg.Trigger) != True:
                        del order
                        collect()
                        delay.delay(cfg.open_order_interval)
                        continue

                else:
                    # fine tune TPSL
                    if client.set_TPSL(order.sym, order.side, order.TP, order.SL, cfg.Trigger) != True:
                        del order
                        collect()
                        delay.delay(cfg.open_order_interval)
                        continue
                            
                log.log_and_show('Entry pirce : {}'.format(order.price))
                if cfg.Trailing_Stop != 0:
                    log.log_and_show('TP : {},  SL : {},  Trailing stop : {}\n'.format(order.TP, order.SL, order.trailing))
                else:
                    log.log_and_show('TP : {},  SL : {}\n'.format(order.TP, order.SL))

                del order
                collect()
                delay.delay(cfg.open_order_interval)
            else:
                if not pnl.start_track_pnl:
                    pnl.start_track_pnl = True
                
                if Pause_place_order and current_position_qty < cfg.Max_operate_position:
                    System_Msg('Available balance lower than stop operate limit!!\nPause place order!!')

                delay.anima_runtime(cfg.poll_order_interval, Start_time)


        except Exception as Err:
            log.show('')
            Error_Msg((str)(Err))
            os.system('pause')
            os._exit(0)