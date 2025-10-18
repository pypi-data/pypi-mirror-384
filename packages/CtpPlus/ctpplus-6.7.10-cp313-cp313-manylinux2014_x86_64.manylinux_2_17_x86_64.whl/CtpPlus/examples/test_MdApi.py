# -*- codeing:utf-8 -*-
'''
@author: jiaoyulong
@datetime: 2024/2/22 11:00
@Blog:
'''
from CtpPlus.CTP.ApiStruct import ReqUserLoginField, QryMulticastInstrumentField
from CtpPlus.CTP.FutureAccount import get_simulate_account, FutureAccount
from CtpPlus.CTP.MdApi import run_api
from CtpPlus.CTP.MdApiBase import MdApiBase


class TickEngine(MdApiBase):
    def __init__(self, broker_id, md_server, investor_id, password, app_id, auth_code, instrument_id_list,
                 md_queue_list=None, page_dir='', using_udp=False, multicast=False, *args, **kwargs):
        super(TickEngine, self).__init__()

    def OnRtnDepthMarketData(self, pDepthMarketData):
        print(pDepthMarketData)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        self.write_log('OnRspUserLogin', pRspUserLogin)

        # 查询组播行情
        # pQryMulticastInstrument = QryMulticastInstrumentField(TopicID=1001, InstrumentID=b'rb2410')
        # ret = self.ReqQryMulticastInstrument(pQryMulticastInstrument)

    def OnRspQryMulticastInstrument(self, pMulticastInstrument, pRspInfo, nRequestID, bIsLast):
        print(f'OnRspQryMulticastInstrument: {pMulticastInstrument}')


if __name__ == '__main__':
    subscribe_list = [b'ag2408']

    future_account = get_simulate_account(
        investor_id='******',  # SimNow账户
        password='*****',  # SimNow账户密码
        subscribe_list=subscribe_list,  # 合约列表
        server_name='电信1'  # 电信1、电信2、移动、TEST
    )

    run_api(TickEngine, future_account)

