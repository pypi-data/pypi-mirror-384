# -*- codeing:utf-8 -*-
'''
@author:
@datetime: 2024/8/28 11:33
@Blog:
'''

from CtpPlus.CTP.MdApi import run_tick_engine, run_bar_engine

from multiprocessing import Process, Queue

from CtpPlus.CTP.TraderApiBase import TraderApiBase, to_str, to_bytes

from CtpPlus.CTP.FutureAccount import FutureAccount, get_simulate_account


class AuthenticateHelper(TraderApiBase):
    def __init__(self, broker_id, td_server, investor_id, password, app_id, auth_code, md_queue=None, flow_path='',
                 private_resume_type=2, public_resume_type=2):
        pass

    def init_extra(self):
        """
        初始化策略参数
        :return:
        """
        self.parameter_dict = self.md_queue.get(block=False)

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

                volume = 1  # 下单手数（自定义）

                # 买开仓
                self.buy_open(bar['ExchangeID'], bar['InstrumentID'], bar['LastPrice'], volume)

                # 卖开仓
                self.sell_open(bar['ExchangeID'], bar['InstrumentID'], bar['LastPrice'], volume)

                # 买平仓
                # self.buy_close(bar['ExchangeID'], bar['InstrumentID'], bar['LastPrice'], volume)
                #
                # # 卖平仓
                # self.sell_close(bar['ExchangeID'], bar['InstrumentID'], bar['LastPrice'], volume)


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
    # 止盈止损参数
    pl_parameter = {
        'StrategyID': 9,
        'ProfitLossParameter': {
            b'ag2412': {'0': [10], '1': [10]},  # 沪银   # '0'代表止盈, '1'代表止损
            b'SA409': {'0': [20], '1': [20]},   # 纯碱
        },
    }

    # 账户配置
    instrument_id_list = []
    for instrument_id in pl_parameter['ProfitLossParameter']:
        instrument_id_list.append(instrument_id)
    future_account = get_simulate_account(
        investor_id='',  # SimNow账户
        password='',  # SimNow账户密码
        subscribe_list=instrument_id_list,  # 合约列表
        server_name='TEST'  # 电信1、电信2、移动、TEST
    )

    # 共享队列
    share_queue = Queue(maxsize=100)
    share_queue.put(pl_parameter)

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
