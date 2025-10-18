# encoding:utf-8
import copy
import os
import csv
from CtpPlus.CTP.MdApiBase import MdApiBase
from CtpPlus.CTP.FutureAccount import FutureAccount
from CtpPlus.ta.time_bar import tick_to_bar
from CtpPlus.utils.base_field import to_str, to_bytes
from CtpPlus.CTP.ApiStruct import DepthMarketDataField


class TickEngine(MdApiBase):
    def __init__(self, broker_id, md_server, investor_id=b'', password=b'', app_id=b'', auth_code=b'',
                 subscribe_list=None, md_queue_list=None, flow_path='', using_udp=False, multicast=False):
        super(TickEngine, self).__init__()

    def OnRtnDepthMarketData(self, pDepthMarketData):
        # 将行情放入共享队列
        for md_queue in self.md_queue_list:
            md_queue.put(pDepthMarketData)


class BarEngine(MdApiBase):
    def __init__(self, broker_id, md_server, investor_id=b'', password=b'', app_id=b'', auth_code=b'',
                 subscribe_list=None, md_queue_list=None, flow_path='', using_udp=False, multicast=False):
        super(BarEngine, self).__init__()

    def init_extra(self):
        # Bar字段
        bar_cache = {
            "ExchangeID": b"",
            "UpdateTime": b"99:99:99",
            "InstrumentID": b"",
            "LastPrice": 0.0,
            "HighPrice": 0.0,
            "LowPrice": 0.0,
            "OpenPrice": 0.0,
            "BarVolume": 0,
            "BarTurnover": 0.0,
            "BarSettlement": 0.0,
            "BVolume": 0,
            "SVolume": 0,
            "FVolume": 0,
            "DayVolume": 0,
            "DayTurnover": 0.0,
            "DaySettlement": 0.0,
            "OpenInterest": 0.0,
            "LastVolume": 0,
            "TradingDay": b"99999999",
        }

        self.bar_dict = {}  # Bar字典容器
        # 遍历订阅列表
        for instrument_id in self.instrument_id_list:
            # 将str转为byte
            if not isinstance(instrument_id, bytes):
                instrument_id = to_bytes(instrument_id.encode('utf-8'))

            # 初始化Bar字段
            bar_cache["InstrumentID"] = instrument_id
            self.bar_dict[instrument_id] = bar_cache.copy()

    # ///深度行情通知
    def OnRtnDepthMarketData(self, pDepthMarketData):
        bar_data = self.bar_dict[pDepthMarketData['InstrumentID']]
        last_update_time = bar_data["UpdateTime"]
        is_new_1minute = (to_str(pDepthMarketData['UpdateTime'])[:-3] != to_str(last_update_time)[:-3]) and to_str(pDepthMarketData['UpdateTime'])[:5] not in ['21:00', '09:00', '13:30']  # 1分钟K线条件
        # is_new_5minute = is_new_1minute and int(to_str(pDepthMarketData['UpdateTime'])[-5:-3]) % 5 == 0 and to_str(pDepthMarketData['UpdateTime'])[:-3] not in ['21:00', '09:00', '10:30', '13:00']  # 5分钟K线条件
        # is_new_10minute = is_new_1minute and int(to_str(pDepthMarketData['UpdateTime'])[-4:-3]) == 0 and to_str(pDepthMarketData['UpdateTime'])[:-3] not in ['21:00', '09:00', '10:30', '13:00']  # 10分钟K线条件
        # is_new_15minute = is_new_1minute and int(to_str(pDepthMarketData['UpdateTime'][-5:-3])) % 15 == 0 and to_str(pDepthMarketData['UpdateTime'])[:-3] not in ['21:00', '09:00', '10:30', '13:00']  # 15分钟K线条件
        # is_new_30minute = is_new_1minute and to_str(pDepthMarketData['UpdateTime'][:-3]) in \
        #                   ['21:30', '22:00', '22:30', '23:00', '23:30', '00:00', '00:30', '01:00', '01:30', '02:00',
        #                    '02:30', '09:30', '10:00', '10:45', '11:15', '13:45', '14:15', '14:45', '15:00']  # 30分钟K线条件

        # if to_str(pDepthMarketData['InstrumentID'])[:2] in ['sc', 'ag', 'au']:
        #     """夜盘到02:30的品种"""
        #     is_new_hour = is_new_1minute and to_str(pDepthMarketData['UpdateTime'][:-3]) in \
        #                   ['22:00', '23:00', '00:00', '01:00', '02:00', '09:30', '10:45', '13:45', '14:45', '15:00'] # 60分钟K线条件
        # else:
        #     is_new_hour = is_new_1minute and to_str(pDepthMarketData['UpdateTime'][:-3]) in \
        #                   ['22:00', '23:00', '00:00', '01:00', '10:00', '11:15', '14:15', '15:00']  # 60分钟K线条件

        # 新K线开始
        if is_new_1minute and last_update_time != b"99:99:99":
            for md_queue in self.md_queue_list:
                md_queue.put(copy.deepcopy(bar_data))

        # 将Tick池化为Bar
        tick_to_bar(bar_data, pDepthMarketData, is_new_1minute)


class MdRecorder(MdApiBase):
    def __init__(self, broker_id, md_server, investor_id, password, app_id, auth_code, instrument_id_list, md_queue_list=None, page_dir='', using_udp=False, multicast=False):
        pass

    def init_csv_files(self):
        self.csv_file_dict = {}
        self.csv_writer = {}
        # 深度行情结构体字段名列表
        header = list(DepthMarketDataField().to_dict())
        for instrument_id in self.subscribe_list:
            instrument_id = to_str(instrument_id)
            # file object
            file_dir = os.path.join(self.flow_path, f'{instrument_id}-{self.GetTradingDay()}.csv')
            self.csv_file_dict[instrument_id] = open(file_dir, 'a', newline='')
            # writer object
            self.csv_writer[instrument_id] = csv.DictWriter(self.csv_file_dict[instrument_id], header)
            # 写入表头
            self.csv_writer[instrument_id].writeheader()
            self.csv_file_dict[instrument_id].flush()

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        self.write_log('OnRspUserLogin', pRspInfo, f'RequestID:{nRequestID}', f'IsLast:{bIsLast}', pRspUserLogin)

        if bIsLast and (not pRspInfo or pRspInfo['ErrorID'] == 0):
            self.init_csv_files()

            error_id = 0
            if self.subscribe_list:
                error_id = self.SubscribeMarketData(self.subscribe_list)
                if error_id != 0:
                    self.write_log('SubscribeMarketData',
                                   {'ErrorID': error_id, 'ErrorMsg': 'Error:Fail to SubscribeMarketData.'},
                                   self.subscribe_list)

            if error_id == 0:
                self.status = 0
                self.write_log('Md Ready!', f'CTP Md API Version:{MdApiBase.GetApiVersion(self)}',
                               f'TradingDay:{self.GetTradingDay()}',
                               f'broker_id:{self.broker_id}', f'server:{self.md_server}',
                               f'subscribe_list:{self.subscribe_list}')

    # ///深度行情通知
    def OnRtnDepthMarketData(self, pDepthMarketData):
        for key in pDepthMarketData.keys():
            pDepthMarketData[key] = to_str(pDepthMarketData[key])
        # 写入行情
        self.csv_writer[pDepthMarketData['InstrumentID']].writerow(pDepthMarketData)
        self.csv_file_dict[pDepthMarketData['InstrumentID']].flush()


def run_api(api_cls, account, md_queue_list=None):
    if isinstance(account, FutureAccount):
        tick_engine = api_cls(
            account.broker_id,
            account.server_dict['MDServer'],
            account.investor_id,
            account.password,
            account.app_id,
            account.auth_code,
            account.subscribe_list,
            md_queue_list,
            account.md_flow_path,
            account.td_flow_path
        )
        tick_engine.Join()


def run_tick_engine(account, md_queue_list):
    run_api(TickEngine, account, md_queue_list)


def run_bar_engine(account, md_queue_list):
    run_api(BarEngine, account, md_queue_list)


def run_mdrecorder(account):
    run_api(MdRecorder, account, None)
