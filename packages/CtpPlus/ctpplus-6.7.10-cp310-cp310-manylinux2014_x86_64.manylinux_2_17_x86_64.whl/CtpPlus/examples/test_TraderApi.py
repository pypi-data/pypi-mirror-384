# -*- codeing:utf-8 -*-
'''
@author: jiaoyulong
@datetime: 2024/3/4 9:56
@Blog:
'''
import time

from CtpPlus.CTP.ApiStruct import QryRULEIntraParameterField, QryProductGroupField, QryExchangeField, \
    QryInstrumentField, FrontInfoField
from CtpPlus.CTP.FutureAccount import get_simulate_account, FutureAccount
from CtpPlus.CTP.TraderApiBase import TraderApiBase
from CtpPlus.utils.base_field import to_str


class TraderEngine(TraderApiBase):
    def __init__(self, broker_id, td_server, investor_id, password, app_id, auth_code, md_queue=None, flow_path='', private_resume_type=2, public_resume_type=2):
        super(TraderEngine, self).__init__()

    def OnRspSettlementInfoConfirm(self, pSettlementInfoConfirm, pRspInfo, nRequestID, bIsLast):
        """投资者结算结果确认响应"""
        self.write_log('pSettlementInfoConfirm', pSettlementInfoConfirm)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登录请求响应"""
        self.write_log('OnRspUserLogin', pRspUserLogin)

        # 获取已连接得前置的信息
        # pfrontInfo = FrontInfoField()
        # result = self.GetFrontInfo(pfrontInfo)
        # self.write_log('GetFrontInfo', result)

        # 请求RULE品种内对锁仓折扣参数查询
        # pQryRULEIntraParameter = QryRULEIntraParameterField(ExchangeID=b'9080', ProdFamilyCode=b'MA')
        # ret = self.ReqQryRULEIntraParameter(pQryRULEIntraParameter)
        # print(f'ReqQryRULEIntraParameter: ret = {ret}')

        # 请求查询产品组
        # pQryProductGroup = QryProductGroupField(ProductID=b'ag', ExchangeID=b'SHFE')
        # ret = self.ReqQryProductGroup(pQryProductGroup)
        # print(f'ReqQryProductGroup: ret = {ret}')

    def Join(self, *args, **kwargs):
        while True:
            # 买开仓
            ret = self.buy_open(b'SHFE', b'rb2405', 3720, 1)
            if not ret:
                self.write_log("ReqOrderInsert", "买入开仓成功")

            """查询持仓明细"""
            # self.query_position_detail()

            """请求查询交易所"""
            # pQryExchange = QryExchangeField(ExchangeID=b'SHFE')
            # self.ReqQryExchange(pQryExchange)

            """请求查询合约，填空可以查询到所有合约"""
            # pQryInstrument = QryInstrumentField()
            # self.ReqQryInstrument(pQryInstrument)
            # self.query_instrument()

            time.sleep(10)

    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        """请求查询合约响应"""
        pInstrument['InstrumentName'] = to_str(pInstrument['InstrumentName'])
        self.write_log("OnRspQryInstrument", pInstrument, pRspInfo)

    def OnRspQryRULEIntraParameter(self, pRULEIntraParameter, pRspInfo, nRequestID, bIsLast):
        self.write_log('OnRspQryRULEIntraParameter', pRULEIntraParameter)

    def OnRspQryProductGroup(self, pProductGroup, pRspInfo, nRequestID, bIsLast):
        self.write_log('OnRspQryProductGroup', pProductGroup, pRspInfo, nRequestID, bIsLast)

    def OnRspQryExchange(self, pExchange, pRspInfo, nRequestID, bIsLast):
        pExchange['ExchangeName'] = to_str(pExchange['ExchangeName'])
        self.write_log('OnRspQryExchange', pExchange)


def run_api(api_cls, account):
    if isinstance(account, FutureAccount):
        trader_engine = api_cls(
            account.broker_id,
            account.server_dict['TDServer'],
            account.investor_id,
            account.password,
            account.app_id,
            account.auth_code,
            None,
            account.td_flow_path
        )
        trader_engine.Join()


if __name__ == '__main__':
    subscribe_list = [b'rb2510']

    future_account = get_simulate_account(
        investor_id='',  # SimNow账户
        password='',  # SimNow账户密码
        subscribe_list=subscribe_list,  # 合约列表
        server_name='电信1'  # 电信1、电信2、移动、TEST、实盘
    )

    run_api(TraderEngine, future_account)
