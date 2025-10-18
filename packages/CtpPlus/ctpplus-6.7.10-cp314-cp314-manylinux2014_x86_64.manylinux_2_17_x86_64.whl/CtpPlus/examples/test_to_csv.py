# -*- codeing:utf-8 -*-
'''
@author:
@datetime: 2024/8/28 11:33
@Blog:
'''
import csv
import os

import pandas as pd

from CtpPlus.CTP.MdApi import run_tick_engine, run_bar_engine

from multiprocessing import Process, Queue

from CtpPlus.CTP.TraderApiBase import TraderApiBase, to_str, to_bytes

from CtpPlus.CTP.FutureAccount import FutureAccount, get_simulate_account


def to_csv(bar):
    """将bar数据保存至本地"""
    bar['ExchangeID'] = to_str(bar['ExchangeID'])
    bar['InstrumentID'] = to_str(bar['InstrumentID'])
    bar['UpdateTime'] = to_str(bar['UpdateTime'])
    bar['TradingDay'] = to_str(bar['TradingDay'])
    bar['ActionDay'] = to_str(bar['ActionDay'])
    file_name = '.'.join([bar['InstrumentID'], 'csv'])
    flag = os.path.exists(f'./{file_name}')
    print(os.path.join(os.getcwd(), file_name))
    with open(file_name, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=bar.keys())
        if not flag:
            # 写入表头
            writer.writeheader()

        writer.writerow(bar)


def read_csv(file_name):
    """读取csv文件数据"""
    df = pd.read_csv(file_name, encoding='utf-8')
    return df


class AuthenticateHelper(TraderApiBase):
    def __init__(self, broker_id, td_server, investor_id, password, app_id, auth_code, md_queue=None, flow_path='',
                 private_resume_type=2, public_resume_type=2):
        pass

    def init_extra(self):
        """
        初始化策略参数
        :return:
        """
        pass

    def OnRtnInstrumentStatus(self, pInstrumentStatus):
        pass

    def OnRtnOrder(self, pOrder):
        self.write_log('OnRtnOrder', pOrder)

    def OnRtnTrade(self, pTrade):
        self.write_log('OnRtnTrade', pTrade)

    def Join(self):
        while True:
            if self.md_queue.empty():
                continue
            else:
                bar = self.md_queue.get(block=False)
                print(bar)  # 打印k线数据

                to_csv(bar)


def run_td_api(api_cls, account, md_queue=None):
    if isinstance(account, FutureAccount):
        trader_engine = api_cls(
            account.broker_id,
            account.server_dict['TDServer'],
            account.investor_id,
            account.password,
            account.app_id,
            account.auth_code,
            md_queue,
            account.td_flow_path
        )
        trader_engine.Join()


def run_trader_engine(account, md_queue=None):
    run_td_api(AuthenticateHelper, account, md_queue)


if __name__ == '__main__':
    # 账户配置
    instrument_id_list = [b'ag2510', b'SA509']
    future_account = get_simulate_account(
        investor_id='',  # SimNow账户
        password='',  # SimNow账户密码
        subscribe_list=instrument_id_list,  # 合约列表
        server_name='TEST'  # 电信1、电信2、移动、TEST
    )

    # 共享队列
    share_queue = Queue(maxsize=100)

    # 行情进程
    md_process = Process(target=run_bar_engine, args=(future_account, [share_queue]))  # 合成k线
    # md_process = Process(target=run_tick_engine, args=(future_account, [share_queue]))  # tick数据
    # 交易进程
    trader_process = Process(target=run_trader_engine, args=(future_account, share_queue))

    #
    md_process.start()
    trader_process.start()

    #
    md_process.join()
    trader_process.join()
