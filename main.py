from time import localtime
from time import strftime
from time import time
from datetime import datetime
import sys
import os
import json
from gc import collect
import random
random.seed()
import csv
from shutil import rmtree
from shutil import copytree

from Make_log import Log
from Loading_animation import delay_anima
from client import Client_USDT_Perpetual

os.system('cls')
##########################################################
Version = '0.7.160'
Date = '2021/12/17'

Symbol_List = {}
Detention_List = {}

delay = delay_anima()

Pause_place_order = False

##############################################################################################################################
### init log
log = Log('log')
log.log('\n=============================START==============================')
log.log_and_show('Bybit USDT perpetual trading bot ver {} {}'.format(Version, Date))

class Open:
    def __init__(self) -> None:
        self.sym = ''
        self.last_price = 0
        self.mark_price = 0
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
        self.total_pnl = 0
        self.total_pnl_rate = 0
        self.track_list = {}
        
        self.start_balance = 'start'
        self.current_balance = 0
        self.start_time = int(time())

        self.dir = dir

    def load(self):
        if not os.path.isfile('{}/pnl.json'.format(self.dir)):
            return

        with open('{}/pnl.json'.format(self.dir), 'r') as file:
            self.temp = json.load(file)
        try:
            self.total_pnl = self.temp['total_pnl']
            self.total_pnl_rate = self.temp['total_pnl_rate']
            self.start_balance = self.temp['start_balance']
            self.current_balance = self.temp['current_balance']
            self.start_time = self.temp['start_time']
        except KeyError:
            self.total_pnl = 0
            self.total_pnl_rate = 0            
            self.start_balance = 'start'
            self.current_balance = 0
            self.start_time = int(time())

        del self.temp        
        
    def write_pnl(self):
        self.temp = {
            'total_pnl' :  self.total_pnl,
            'total_pnl_rate' :  self.total_pnl_rate,
            'start_balance' :  self.start_balance,
            'current_balance' :  self.current_balance,
            'start_time' : self.start_time
        }
        
        with open('{}/pnl.json'.format(self.dir), 'w') as file:
            json.dump(self.temp, file, indent = 4)

        del self.temp
    
    def record_balance(self):
        if not os.path.isfile('{}/balance.csv'.format(self.dir)):
            with open('{}/balance.csv'.format(self.dir), 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['time', 'balance'])
        
        with open('{}/balance.csv'.format(self.dir), 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([(int)(time()), self.current_balance])
    
    def write_position_list(self):
        with open('{}/posi.json'.format(self.dir), 'w') as file:
            json.dump(self.track_list, file, indent = 4)

    def load_position_list(self):
        try:
            with open('{}/posi.json'.format(self.dir), 'r') as file:
                self.track_list = json.load(file)
            return True
        except:
            return False

class CFG:
    def __init__(self, version) -> None:
        self.version = version
        self.Test_net = True
        self.Max_operate_position = None
        self.operate_USDT = None
        self.stop_operate_USDT = None
        self.press_the_winned_USDT = None
        self.press_the_winned_thres = None
        self.Leverage = None
        self.side = None
        self.TP_percentage = None
        self.SL_percentage = None
        self.Trigger = None
        self.Trailing_Stop = None
        self.position_expire_time = None
        self.position_expire_thres = None
        self.Group = None
        self.open_order_interval = None
        self.poll_order_interval = None
        self.detention_time = None
        self.Token_list = []
        self.Black_list = []
        self.Retry_times = None
        self.Retry_delay = None
        
        self.cfg_init = {
                            'Version' : Version,
                            'Run_on_testnet' : True,
                            'Operate_position' : 2,
                            'Order_value_USDT' : 10,
                            'Stop_operate_USDT' : 10,
                            'Press_the_winned_USDT' : 0,
                            'Press_the_winned_thres_percentag' : 0,
                            'Leverage' : 20,
                            'Side' : 'Both',
                            'TP_percentage' : 100,
                            'SL_percentage' : 10,
                            'Trigger' : 'LastPrice',
                            'Trailing_Stop_percentag' : 0,
                            'Position_expire_time' : 0,
                            'Position_expire_thres_percentag' : 0,
                            'Opreate_group' : 'all',
                            'Open_interval' : 1,
                            'Poll_interval' : 60,
                            'Detention_time' : 86400,
                            'Black_list' : [],
                            'Group_0' : [
                                'BTC',  'ETH',  'DOT',  'SOL',
                                'BNB',  'FTT',  'UNI',  'AXS',
                                'LUNA', 'ATOM', 'AAVE', 'FTM',
                                'BIT',  'ADA',  'ICP'
                                ],
                            'Retry_times' : 30,
                            'Retry_delay' : 0.2
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
            self.Max_operate_position = abs(self.cfg['Operate_position'])
            self.operate_USDT = abs(self.cfg['Order_value_USDT'])
            self.stop_operate_USDT = abs(self.cfg['Stop_operate_USDT'])
            self.press_the_winned_USDT = abs(self.cfg['Press_the_winned_USDT'])
            self.press_the_winned_thres = abs(self.cfg['Press_the_winned_thres_percentag'])
            self.Leverage = abs(self.cfg['Leverage'])
            self.side = self.cfg['Side']
            self.TP_percentage = abs(self.cfg['TP_percentage'])
            self.SL_percentage = abs(self.cfg['SL_percentage'])
            self.Trigger = self.cfg['Trigger']
            self.Trailing_Stop = abs(self.cfg['Trailing_Stop_percentag'])
            self.position_expire_time = abs(self.cfg['Position_expire_time'])
            self.position_expire_thres = self.cfg['Position_expire_thres_percentag']

            self.Group = self.cfg['Opreate_group']
            self.open_order_interval = abs(self.cfg['Open_interval'])
            self.poll_order_interval = abs(self.cfg['Poll_interval'])
            self.detention_time = abs(self.cfg['Detention_time'])
            self.Black_list.clear()
            for i in self.cfg['Black_list']:
                self.Black_list.append('{}USDT'.format(i))

            self.Token_list.clear()
            if self.Group in self.cfg and self.Group != 'Black_list':
                for i in self.cfg[self.Group]:
                    self.Token_list.append('{}USDT'.format(i))
            else:
                self.Group = 'all'

            self.Retry_times = abs(self.cfg['Retry_times'])
            self.Retry_delay = abs(self.cfg['Retry_delay'])

            return True
        
        except KeyError:
            self.archive_cfg('cfg.json corrupted, old one archive as cfg_{}.json'.format(timestamp_format(os.path.getctime('cfg.json'), '%Y%m%d-%H;%M;%S')))
    
    def update_version(self):
        self.version = Version
        self.cfg['Version'] = self.version
        with open('cfg.json', 'w') as file:
            json.dump(self.cfg, file, indent = 4)
    
    def upgrade_cfg(self):
        System_Msg('cfg.json upgraded, old one archive as cfg_{}.json'.format(timestamp_format(os.path.getctime('cfg.json'), '%Y%m%d-%H;%M;%S')))
        if not os.path.isdir('archive'):
            os.mkdir('archive')
        os.rename('cfg.json', 'archive/cfg_{}.json'.format(timestamp_format(os.path.getctime('cfg.json'), '%Y%m%d-%H;%M;%S')))

        for i in self.cfg_init:
            if not i in self.cfg:
                self.cfg[i] = self.cfg_init[i]

        self.update_version()

    def archive_cfg(self, msg):
        System_Msg(msg)
        if not os.path.isdir('archive'):
            os.mkdir('archive')
        os.rename('cfg.json', 'archive/cfg_{}.json'.format(timestamp_format(os.path.getctime('cfg.json'), '%Y%m%d-%H;%M;%S')))
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
    rand = random.choice(list(Symbol_List.keys()))
    if Symbol_List[rand]['opened']:
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

def timestamp_format(stamp, format = '%H:%M:%S %Y-%m-%d'):
    return strftime(format, localtime(stamp))

def argv_check():
    if len(sys.argv) < 3:
        log.show('Execution cmd :')
        log.show('main.exe <api key> <api secret> <-R : restart pnl record>')
        os.system('pause')
        os._exit(0)
    elif len(sys.argv[1]) != 18 or len(sys.argv[2]) != 36:
        log.show('Invalid <api key> or <api secret>')
        os.system('pause')
        os._exit(0)

    else:
        #with other cmd
        for i in sys.argv[3:]:
            if not i.startswith('-'):
                sys.argv.pop(sys.argv.index(i))

        cmd = set(sys.argv[3:])

        for i in cmd:
            match i:
                case '-R':                
                    if os.path.isdir('pnl'):
                        if not os.path.isdir('archive'):
                            os.mkdir('archive')
                        copytree('pnl', 'archive/pnl_{}'.format(timestamp_format(os.path.getctime('pnl/balance.csv'), '%Y%m%d-%H;%M;%S')))
                        rmtree('pnl')
                case _:
                    continue    

def detention_release(Detention_time = 86400):
    if len(Detention_List) == 0:
        return
    release = []
    for i in Detention_List:
        if int(time()) - Detention_List[i]['time'] > Detention_time:
            # detention time pass, release back to Symbol_List
            Symbol_List[i] = Detention_List[i]['data']
            release.append(i)
    
    for i in release:
        del Detention_List[i]
    del release
    
if __name__ == '__main__':
    argv_check()

    try:
        ##############################################################################################################################
        ### Load Cfg File
        cfg = CFG(Version)

        if not os.path.isfile('cfg.json'):
            System_Msg('cfg.json file missing. Generate a new one')
            cfg.new_cfg()
            os.system('pause')

        if not cfg.load_cfg():
            if (float)(cfg.version.split('.')[0]) != (float)(Version.split('.')[0]) or \
               (float)(cfg.version.split('.')[1]) != (float)(Version.split('.')[1]):
                # Main version different
                cfg.upgrade_cfg()
                log.show('Upgrade cfg.json, please check new config or press any key to continue')
                os.system('pause')
                cfg.load_cfg()

            elif (float)(cfg.version.split('.')[2]) < (float)(Version.split('.')[2]):
                #Sub version different
                cfg.update_version()
                cfg.load_cfg()
        
        Max_operate_position = cfg.Max_operate_position

        ### Check parameter
        if cfg.press_the_winned_thres == 0:
            cfg.press_the_winned_USDT = 0

        if cfg.stop_operate_USDT < cfg.operate_USDT + cfg.press_the_winned_USDT:
            cfg.stop_operate_USDT = cfg.operate_USDT + cfg.press_the_winned_USDT

        if cfg.open_order_interval < 1:
            cfg.open_order_interval = 1
            
        if cfg.poll_order_interval < 10:
            cfg.poll_order_interval = 10

        if cfg.side != 'Buy' and cfg.side != 'Sell':
            cfg.side = 'Both'

        if cfg.Trigger != 'MarkPrice' and cfg.Trigger != 'LastPrice' and cfg.Trigger != 'IndexPrice':
            cfg.Trigger = 'LastPrice'

        if cfg.position_expire_thres > cfg.TP_percentage:
            cfg.position_expire_time = 0

        if cfg.position_expire_time != 0 and cfg.position_expire_time < cfg.poll_order_interval:
            cfg.position_expire_time = cfg.poll_order_interval

        if cfg.Retry_times < 10:
            cfg.Retry_times = 10

        if cfg.Retry_delay < 0.1:
            cfg.Retry_delay = 0.1
        
        log.log('cfg.json loaded\n\tVersion: {}\n\tRun on test net: {}\n\tOperate position: {}\n\tOperate USDT: {}\n'.format(cfg.version, cfg.Test_net, cfg.Max_operate_position, cfg.operate_USDT) +\
                '\tStop_operate_USDT: {}\n\tPress_the_winned_USDT: {}\n\tPress_the_winned_thres_percentag: {}%\n'.format(cfg.stop_operate_USDT, cfg.press_the_winned_USDT, cfg.press_the_winned_thres) +\
                '\tLeverage: {}\n\tOperate side: {}\n\tTP: {}%\n\tSL: {}%\n'.format(cfg.Leverage, cfg.side, cfg.TP_percentage, cfg.SL_percentage) +\
                '\tTPSL trigger: {}\n\tTrailing stop: {}%\n'.format(cfg.Trigger, cfg.Trailing_Stop) +\
                '\tPosition_expire_time: {}s\n\tPosition_expire_thres_percentag: {}%\n'.format(cfg.position_expire_time, cfg.position_expire_thres) +\
                '\tOperate group: {}\n\tOpen order interval: {}s\n\tPolling interval: {}s\n'.format(cfg.Group, cfg.open_order_interval, cfg.poll_order_interval) +\
                '\tDetention_time: {}s\n\tRetry_times: {}\n\tRetry_delay: {}'.format(cfg.detention_time, cfg.Retry_times, cfg.Retry_delay))

        ##############################################################################################################################
        ### Load history pnl data and init log    
        pnl = PNL_data('pnl')
        pnl.load()

        ##############################################################################################################################
        ### Create client
        if cfg.Test_net:
            log.log('Run on Test Net !!!')
            client = Client_USDT_Perpetual('https://api-testnet.bybit.com', api_key = sys.argv[1], api_secret = sys.argv[2])
        else:
            log.log('Run on Main Net !!!')
            client = Client_USDT_Perpetual('https://api.bybit.com', api_key = sys.argv[1], api_secret = sys.argv[2])

        ### Query and Check Sym list
        Symbol_query = client.query_symbol()
        if Symbol_query == False:
            raise Exception('Query symbol Faill!!')

        symbol_temp = []
        if cfg.Group == 'all':
            for i in Symbol_query:
                if not i['name'] in cfg.Black_list:
                    Symbol_List[i['name']] = {
                        'tick_size' : float(i['price_filter']['tick_size']),
                        'qty_step' : float(i['lot_size_filter']['qty_step']),
                        'opened' : False,
                        'isolate' : False,
                        'leverage' : 0,
                        'tpsl_mode' : 'Partial'
                    }
                    symbol_temp.append('"{}",\n'.format(i['name']))
        else:
            for i in Symbol_query:
                if i['name'] in cfg.Token_list and not i['name'] in cfg.Black_list:
                    Symbol_List[i['name']] = {
                        'tick_size' : float(i['price_filter']['tick_size']),
                        'qty_step' : float(i['lot_size_filter']['qty_step']),
                        'opened' : False,
                        'isolate' : False,
                        'leverage' : 0,
                        'tpsl_mode' : 'Partial'
                    }
                    symbol_temp.append('"{}",\n'.format(i['name']))
        del Symbol_query

        with open('pnl/trade_symbol.log', 'w') as file:
            file.write('{}\tTrading symbols\n'.format(len(symbol_temp)))
            file.writelines(symbol_temp)
        del file
        del symbol_temp

    except Exception as Err:
        Err = str(Err)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log.show('')
        Error_Msg(Err)
        log.log('Exception type: {}, in: <{}>, line: {}'.format(exc_type, fname, exc_tb.tb_lineno))
        os.system('pause')
        os._exit(0)

    while True:
        try:
            log.log_and_show(log.get_run_time(pnl.start_time))

            ### Check if eligible symbol qty exceed max operated qty
            if cfg.Max_operate_position > len(Symbol_List):
                if Max_operate_position > len(Symbol_List):
                    System_Msg('Max_operate_position exceed symbol white list qty\nDecrease Max_operate_position form {} to {}'\
                                .format(Max_operate_position, len(Symbol_List)))
                    Max_operate_position = len(Symbol_List)
                elif Max_operate_position < len(Symbol_List):
                    System_Msg('Symbol white list qty added\nIncrease Max_operate_position form {} to {}'\
                                .format(Max_operate_position, len(Symbol_List)))
                    Max_operate_position = len(Symbol_List)
            elif cfg.Max_operate_position != Max_operate_position:
                Max_operate_position = cfg.Max_operate_position



            ### Query current wallet balance
            wallet = client.get_wallet_balance()
            if wallet != False:
                wallet_available = wallet['available_balance']
                wallet_equity = wallet['equity']
                # wallet_real_pnl = wallet['realised_pnl']
                # wallet_cum_pnl = wallet['cum_realised_pnl']

                if pnl.start_balance == 'start':
                    pnl.start_balance = wallet_equity

                pnl.current_balance = wallet_equity
                pnl.total_pnl = pnl.current_balance - pnl.start_balance
                if pnl.start_balance != 0:
                    pnl.total_pnl_rate = pnl.total_pnl * 100 / pnl.start_balance
                else:
                    pnl.total_pnl_rate = 0

                pnl.write_pnl()
                pnl.record_balance()
                
                log.log_and_show('Start wallet balance: {: 13.2f}\tUSDT\n'.format(pnl.start_balance) +\
                                'Balance available:\t {: 13.2f}\tUSDT\nBalance equity:\t {: 13.2f}\tUSDT\n'.format(wallet_available, wallet_equity) +\
                                'Unrealized pnl:\t {: 13.2f}\tUSDT, {: .2f}%'.format(pnl.total_pnl, pnl.total_pnl_rate))
                log.show('')

                if wallet_available < cfg.stop_operate_USDT:
                    Pause_place_order = True
                else:
                    Pause_place_order = False

            del wallet

            ### Query current position
            current_position_qty = 0
            current_position_buy = 0
            current_position_sell = 0
            Position_List = {}
            opened_position = {}
            
            position = client.get_all_position()
            
            for i in position['result']:
                if i['is_valid']:
                    if not i['data']['symbol'] in Position_List:
                        Position_List[i['data']['symbol']] = {i['data']['side'] : i['data']}
                    else:
                        Position_List[i['data']['symbol']][i['data']['side']] = i['data']
                else:
                    Error_Msg('{} {} position data NOT valid'.format(i['data'][' '], i['data']['side']))
            
            ### Chek position status
            for i in Position_List:
                temp = Symbol_List.get(i, False)
                if temp == False:
                    continue

                if Position_List[i]['Buy']['is_isolated'] and Position_List[i]['Sell']['is_isolated']:
                    temp['isolate'] = True
                else:
                    temp['isolate'] = False
                
                if Position_List[i]['Buy']['leverage'] == cfg.Leverage and Position_List[i]['Sell']['leverage'] == cfg.Leverage:
                    temp['leverage'] = cfg.Leverage
                else:
                    temp['leverage'] = 0

                if Position_List[i]['Buy']['tp_sl_mode'] == 'Full' and Position_List[i]['Sell']['tp_sl_mode'] == 'Full':
                    temp['tpsl_mode'] = 'Full'
                else:
                    temp['tpsl_mode'] = 'Partial'
                
                if Position_List[i]['Buy']['position_value'] > 0:
                    temp['opened'] = True
                    opened_position[i] = {'side' : 'Buy'}
                elif Position_List[i]['Sell']['position_value'] > 0:
                    temp['opened'] = True
                    opened_position[i] = {'side' : 'Sell'}
                else:
                    temp['opened'] = False
                Symbol_List[i] = temp
                        
            ### track opened position
            if len(pnl.track_list) == 0 and len(opened_position) != 0:
                # start peogram with on going position
                if not pnl.load_position_list():
                    pnl.track_list = opened_position
                    for i in pnl.track_list:
                        if not 'time' in pnl.track_list[i]:
                            pnl.track_list[i]['time'] = int(time())
                        if not 'pressed' in pnl.track_list[i]:
                            pnl.track_list[i]['pressed'] = False

                if len(opened_position) >= Max_operate_position:
                    # position opening done start track
                    pnl.start_track_pnl = True
            
            delete_list = []
            if pnl.start_track_pnl:
                pnl.load_position_list()

                for i in pnl.track_list:
                    if i in opened_position:
                        # position still going
                        price = client.get_last_price(i)
                        if price == False:
                            del price
                            pnl.track_list[i]['pnl'] = 0
                            delay.delay(0.05)
                            continue
                        
                        match cfg.Trigger:
                            case 'LastPrice':
                                posi_pnl = float(price['last_price']) - Position_List[i][pnl.track_list[i]['side']]['entry_price']
                            case 'MarkPrice':
                                posi_pnl = float(price['mark_price']) - Position_List[i][pnl.track_list[i]['side']]['entry_price']
                            case 'IndexPrice':
                                posi_pnl = float(price['index_price']) - Position_List[i][pnl.track_list[i]['side']]['entry_price']
                            
                        posi_pnl = posi_pnl * cfg.Leverage * 100 / Position_List[i][pnl.track_list[i]['side']]['entry_price']

                        if pnl.track_list[i]['side'] == 'Sell':
                            posi_pnl *= -1

                        last_price = float(price['last_price'])
                        mark_price = float(price['mark_price'])                        
                        pnl.track_list[i]['pnl'] = posi_pnl
                        del price

                        if cfg.position_expire_time != 0 and (time() - pnl.track_list[i]['time']) > cfg.position_expire_time:
                            # position expire if position_expire_time had set, check pnl
                            if posi_pnl < cfg.position_expire_thres:
                                # pnl lesser than threshold, start closaing it
                                log.log_and_show('{} {} position expired, pnl {: .2f}%'.format(i, pnl.track_list[i]['side'], posi_pnl))
                                place_order = client.place_order(i, pnl.track_list[i]['side'],  Position_List[i][pnl.track_list[i]['side']]['size'], 0, 0, True)
                                if place_order == False or place_order == '130023':
                                    # Will lqt right after position placed
                                    del place_order
                                    continue
                                elif place_order == '130021':
                                    # Under balance, stop open order
                                    Pause_place_order = True
                                    del place_order
                                    continue
                                else:
                                    if place_order['ret_msg'] != 'OK':
                                        System_Msg('{} close order create successfully !!\nwith return msg: {}'.format(i, place_order['ret_msg']))
                                    else:
                                        log.log_and_show('{} close order create successfully !!'.format(i))
                                
                                retry = cfg.Retry_times
                                while retry:
                                    order_status = client.get_order_status(i, place_order['result']['order_id'], )
                                    if order_status != False:
                                        match order_status:
                                            case 'Filled':
                                                log.log('{} close order ''{}'' Filled, retry: {} times'.format(i, place_order['result']['order_id'], cfg.Retry_times - retry))
                                                break
                                            case 'Rejected' | 'Cancelled':
                                                retry = 'F'
                                                break
                                            case _:
                                                pass

                                        retry -= 1
                                        delay.delay(cfg.Retry_delay)
                                    else:
                                        break

                                if retry == 0:
                                    # retry fail
                                    Error_Msg('Close {} position order Fail!! retry: {}, order_status: {}'.format(i, cfg.Retry_times, order_status))
                                    del order_status
                                    del place_order
                                    del retry
                                    continue
                                elif retry == 'F':
                                    # Order status error
                                    Error_Msg('Close {} position order Fail!!, order_status: {}'.format(i, order_status))
                                    del order_status
                                    del place_order
                                    del retry
                                    continue                                    
                                del retry

                                
                                del order_status
                                del place_order
                                delete_list.append(i)
                                log.log_and_show('Close {} position successfully !!'.format(i))
                                delay.delay(cfg.open_order_interval)
                            else:
                                # pnl larger than threshold, renew the time
                                pnl.track_list[i]['time'] = int(time())
                            
                        if cfg.press_the_winned_USDT > 0 and not pnl.track_list[i]['pressed'] and posi_pnl > cfg.press_the_winned_thres:
                            # position still going and need to press the win
                            if not Pause_place_order:
                                log.log_and_show('Add {}\tUSDT to {}\t{} position'.format(cfg.press_the_winned_USDT, i,  pnl.track_list[i]['side']))
                                
                                # Check if MarkPrice and LadtPrice detach exceed SL or TP do not press
                                detach_percentage = abs(last_price - mark_price) / last_price * 100 * cfg.Leverage
                                if detach_percentage > cfg.SL_percentage or detach_percentage > cfg.TP_percentage:
                                    System_Msg('{} MarkPrice and LadtPrice detach exceed too much\nDon''t press'.format(i))
                                    del last_price
                                    del mark_price
                                    del detach_percentage
                                    continue

                                qty = qty_trim((cfg.press_the_winned_USDT * cfg.Leverage / last_price), Symbol_List[i]['qty_step'])
                                del last_price
                                del mark_price
                                del detach_percentage

                                place_order = client.place_order(i, pnl.track_list[i]['side'], qty, Position_List[i][pnl.track_list[i]['side']]['take_profit'], Position_List[i][pnl.track_list[i]['side']]['stop_loss'])
                                if place_order == False or place_order == '130023':
                                    # Will lqt right after position placed
                                    del place_order
                                    continue
                                elif place_order == '130021':
                                    # Under balance, stop open order
                                    Pause_place_order = True
                                    del place_order
                                    continue
                                else:
                                    del qty
                                    if place_order['ret_msg'] != 'OK':
                                        System_Msg('{} press order create successfully !!\nwith return msg: {}'.format(i, place_order['ret_msg']))
                                    else:
                                        log.log_and_show('{} press order create successfully !!'.format(i))

                                retry = cfg.Retry_times
                                while retry:
                                    order_status = client.get_order_status(i, place_order['result']['order_id'], )
                                    if order_status != False:
                                        match order_status:
                                            case 'Filled':
                                                log.log('{} press order ''{}'' Filled, retry: {} times'.format(i, place_order['result']['order_id'], cfg.Retry_times - retry))
                                                break
                                            case 'Rejected' | 'Cancelled':
                                                retry = 'F'
                                                break
                                            case _:
                                                pass

                                        retry -= 1
                                        delay.delay(cfg.Retry_delay)
                                    else:
                                        break

                                if retry == 0:
                                    # retry fail
                                    Error_Msg('Press {} position order Fail!! retry: {}, order_status: {}'.format(i, cfg.Retry_times, order_status))
                                    del order_status
                                    del place_order
                                    del retry
                                    continue
                                elif retry == 'F':
                                    # Order status error
                                    Error_Msg('Press {} position order Fail!!, order_status: {}'.format(i, order_status))
                                    del order_status
                                    del place_order
                                    del retry
                                    continue  
                                del retry

                                log.log_and_show('Press {}\t{} position successfully !!'.format(i, pnl.track_list[i]['side']))
                                del order_status
                                del place_order
                                pnl.track_list[i]['pressed'] = True
                                delay.delay(cfg.open_order_interval)
                            
                            else:
                                log.log_and_show('Under balance for press the winned {} !!'.format(i))

                        del posi_pnl
                        delay.delay(0.05)
                        
                    else:
                        # position  closed
                        delete_list.append(i)
            
            for i in delete_list:
                del pnl.track_list[i]

            del delete_list
            del opened_position
            del position
            del Position_List

            current_position_qty = len(pnl.track_list)
            for i in pnl.track_list:
                if pnl.track_list[i]['side'] == 'Buy':
                    current_position_buy += 1
                elif pnl.track_list[i]['side'] == 'Sell':
                    current_position_sell += 1

            pnl.write_pnl()
            pnl.write_position_list()
            
            show = 'Opened Position: {}\tBuy: {} Sell: {}\n'.format(current_position_qty, current_position_buy, current_position_sell)        
            if pnl.start_track_pnl:
                for i in pnl.track_list:
                    show += '\t{} \t{} \t{: 7.2f}%\t'.format(i, pnl.track_list[i]['side'], pnl.track_list[i]['pnl'])
                    if pnl.track_list[i]['pressed']:
                        show += 'Pressed'
                    else:
                        show += '       '
                    show += '\t{}\n'.format(timestamp_format(pnl.track_list[i]['time']))
            log.log_and_show(show)
            del show
            
            ### Randonly open position
            if not Pause_place_order and current_position_qty < Max_operate_position:
                if pnl.start_track_pnl:
                    pnl.start_track_pnl = False
                order = Open()

                # Random pick
                order.sym = rand_symbol()
                if cfg.side == 'Both':
                    order.side = rand_side()
                else:
                    order.side = cfg.side

                # Set Full Position TP/SL
                if Symbol_List[order.sym]['tpsl_mode'] != 'Full':
                    if client.set_tpsl_mode(order.sym) == True:
                        Symbol_List[order.sym]['tpsl_mode'] = 'Full'
                    else:
                        Detention_List[order.sym] = {'data' : Symbol_List.pop(order.sym), 'time' : int(time())}
                        System_Msg('Put {} into detention'. format(order.sym))
                        del order
                        delay.delay(cfg.open_order_interval)
                        continue

                # Switch to isolated margin mode and set leverage
                if Symbol_List[order.sym]['isolate'] != True:
                    if client.set_margin_mode(order.sym, True, cfg.Leverage) == True:
                        Symbol_List[order.sym]['isolate'] = True
                        Symbol_List[order.sym]['leverage'] = cfg.Leverage
                    else:
                        Detention_List[order.sym] = {'data' : Symbol_List.pop(order.sym), 'time' : int(time())}
                        System_Msg('Put {} into detention'. format(order.sym))
                        del order
                        delay.delay(cfg.open_order_interval)
                        continue

                # Modify leverage
                if Symbol_List[order.sym]['leverage'] != cfg.Leverage:
                    if client.set_leverage(order.sym, cfg.Leverage) == True:
                        Symbol_List[order.sym]['leverage'] = cfg.Leverage
                    else:
                        Detention_List[order.sym] = {'data' : Symbol_List.pop(order.sym), 'time' : int(time())}
                        System_Msg('Put {} into detention'. format(order.sym))
                        del order
                        delay.delay(cfg.open_order_interval)
                        continue

                # Query price
                price = client.get_last_price(order.sym)
                if price == False:
                    Detention_List[order.sym] = {'data' : Symbol_List.pop(order.sym), 'time' : int(time())}
                    System_Msg('Put {} into detention'. format(order.sym))
                    del order
                    delay.delay(cfg.open_order_interval)
                    continue
                
                order.last_price = float(price['last_price'])
                order.mark_price = float(price['mark_price'])
                del price

                # Check if MarkPrice and LastPrice detach exceed SL or TP, put into to detention
                detach_percentage = abs(order.last_price - order.mark_price) / order.last_price * 100 * cfg.Leverage
                if detach_percentage > cfg.SL_percentage or detach_percentage > cfg.TP_percentage:
                    Detention_List[order.sym] = {'data' : Symbol_List.pop(order.sym), 'time' : int(time())}
                    System_Msg('MarkPrice and LadtPrice detach exceed too much\nPut {} into detention'. format(order.sym))
                    del order
                    del detach_percentage
                    delay.delay(cfg.open_order_interval)
                    continue
                del detach_percentage

                # Calculate rough TP/SL and qty
                order.qty = qty_trim((cfg.operate_USDT * cfg.Leverage / order.last_price), Symbol_List[order.sym]['qty_step'])
                if order.side == 'Buy':
                    order.TP = price_trim((1 + (cfg.TP_percentage / cfg.Leverage / 100)) * order.last_price, Symbol_List[order.sym]['tick_size'])
                    order.SL = price_trim((1 - (cfg.SL_percentage / cfg.Leverage / 100)) * order.last_price, Symbol_List[order.sym]['tick_size'])
                elif order.side == 'Sell':
                    order.TP = price_trim((1 - (cfg.TP_percentage / cfg.Leverage / 100)) * order.last_price, Symbol_List[order.sym]['tick_size'])
                    order.SL = price_trim((1 + (cfg.SL_percentage / cfg.Leverage / 100)) * order.last_price, Symbol_List[order.sym]['tick_size'])
                
                log.log_and_show('Opening {} {} {} position at about {}'.format(order.qty, order.sym, order.side, order.last_price))

                # Open order
                place_order = client.place_order(order.sym, order.side, order.qty, order.TP, order.SL)
                if place_order == False or place_order == '130023':
                    # Will lqt right after position placed, black list this one
                    Detention_List[order.sym] = {'data' : Symbol_List.pop(order.sym), 'time' : int(time())}
                    System_Msg('Put {} into detention'. format(order.sym))
                    del order
                    delay.delay(cfg.open_order_interval)
                    continue
                elif place_order == '130021':
                    # Under balance, stop open order
                    Pause_place_order = True
                    del order
                    delay.delay(cfg.open_order_interval)
                    continue
                else:
                    if place_order['ret_msg'] != 'OK':
                        System_Msg('{} {} order create successfully !!\nwith return msg: {}'.format(order.sym, order.side, place_order['ret_msg']))
                    else:
                        log.log_and_show('{} {} order create successfully !!'.format(order.sym, order.side))

                    order.order_id = place_order['result']['order_id']
                    pnl.track_list[order.sym] = {'time' : int(time()), 'side' : order.side, 'pressed' : False}
                    pnl.write_position_list()
                    del place_order

                # Get newly placed order status
                retry = cfg.Retry_times
                while retry:
                    order_status = client.get_order_status(order.sym, order.order_id)
                    if order_status != False:
                        match order_status:
                            case 'Filled':
                                log.log('{} {} order ''{}'' Filled, retry: {} times'.format(order.sym, order.side, order.order_id, cfg.Retry_times - retry))
                                break
                            case 'Rejected' | 'Cancelled':
                                retry = 'F'
                                break
                            case _:
                                pass

                        retry -= 1
                        delay.delay(cfg.Retry_delay)
                    else:
                        break

                if retry == 0:
                    # retry fail
                    Error_Msg('Open {} position order Fail!! retry: {}, order_status: {}'.format(order.sym, cfg.Retry_times, order_status))
                    del order
                    del order_status
                    del retry
                    delay.delay(cfg.open_order_interval)
                    continue                
                elif retry == 'F':
                    # Order status error
                    Error_Msg('Open {} position order Fail!!, order_status: {}'.format(order.sym, order_status))
                    del order
                    del order_status
                    del retry
                    delay.delay(cfg.open_order_interval)
                    continue
                del retry

                #Get entry price and Calculate new TP/SL
                order.last_price = client.get_entry_price(order.sym, order.side)
                if order.last_price != False:
                    if order.side == 'Buy':
                        order.TP = price_trim((1 + (cfg.TP_percentage / cfg.Leverage / 100)) * order.last_price, Symbol_List[order.sym]['tick_size'])
                        order.SL = price_trim((1 - (cfg.SL_percentage / cfg.Leverage / 100)) * order.last_price, Symbol_List[order.sym]['tick_size'])
                    elif order.side == 'Sell':
                        order.TP = price_trim((1 - (cfg.TP_percentage / cfg.Leverage / 100)) * order.last_price, Symbol_List[order.sym]['tick_size'])
                        order.SL = price_trim((1 + (cfg.SL_percentage / cfg.Leverage / 100)) * order.last_price, Symbol_List[order.sym]['tick_size'])
                else:
                    del order
                    delay.delay(cfg.open_order_interval)
                    continue
                
                # Calculate and set Trailing stop
                if cfg.Trailing_Stop != 0:
                    order.trailing = price_trim(order.last_price * (cfg.Trailing_Stop / cfg.Leverage / 100), Symbol_List[order.sym]['tick_size'])

                    # Set trailing stop
                    if client.set_trailing_stop(order.sym, order.side, order.trailing, order.TP, order.SL, cfg.Trigger) != True:
                        del order
                        delay.delay(cfg.open_order_interval)
                        continue

                else:
                    # fine tune TPSL
                    if client.set_TPSL(order.sym, order.side, order.TP, order.SL, cfg.Trigger) != True:
                        del order
                        delay.delay(cfg.open_order_interval)
                        continue
                                            
                log.log_and_show('Entry pirce : {}'.format(order.last_price))
                if cfg.Trailing_Stop != 0:
                    log.log_and_show('TP : {},  SL : {},  Trailing stop : {}\n'.format(order.TP, order.SL, order.trailing))
                else:
                    log.log_and_show('TP : {},  SL : {}\n'.format(order.TP, order.SL))

                del order
                delay.delay(cfg.open_order_interval)
            else:
                if not pnl.start_track_pnl:
                    pnl.start_track_pnl = True
                    delay.delay(cfg.open_order_interval)
                    continue
                
                if Pause_place_order and current_position_qty < Max_operate_position:
                    System_Msg('Available balance lower than stop operate limit!!\nPause place order!!')
                
                detention_release(cfg.detention_time)
                
                collect()
                delay.anima_runtime(cfg.poll_order_interval, pnl.start_time)

        except Exception as Err:
            Err = str(Err)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.show('')

            match Err:
                case "('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))":
                    System_Msg(Err)
                    log.log('Exception type: {}, in: <{}>, line: {}'.format(exc_type, fname, exc_tb.tb_lineno))
                    os.system('pause')
                    continue
                case _:
                    Error_Msg(Err)
                    log.log('Exception type: {}, in: <{}>, line: {}'.format(exc_type, fname, exc_tb.tb_lineno))
                    os.system('pause')
                    os._exit(0)
