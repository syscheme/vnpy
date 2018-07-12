# encoding: UTF-8

'''
This module represent an A-Share acount
'''
from __future__ import division

from datetime import datetime, timedelta
from collections import OrderedDict
from itertools import product
import multiprocessing
import copy

import pymongo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 如果安装了seaborn则设置为白色风格
try:
    import seaborn as sns       
    sns.set_style('whitegrid')  
except ImportError:
    pass

from vnpy.trader.vtGlobal import globalSetting
from vnpy.trader.vtObject import VtTickData, VtBarData
from vnpy.trader.vtConstant import *
from vnpy.trader.vtGateway import VtOrderData, VtTradeData

from .Base import *

#----------------------------------------------------------------------
def calculateFee(symbol, price, volumeX1, rate=3/10000):
    # 交易手续费=印花税+过户费+券商交易佣金
    turnOver = price * abs(volumeX1)
    
    # 印花税: 成交金额的1‰ 。目前向卖方单边征收
    tax = 0
    if volumeX1 >0:
        tax = turnOver /1000
        
    #过户费（仅上海收取，也就是买卖上海股票时才有）：每1000股收取1元，不足1000股按1元收取
    transfer =0
    if symbol[1]=='6' or symbol[1]=='7':
        transfer = int((volumeX1+999)/1000)
        
    #3.券商交易佣金 最高为成交金额的3‰，最低5元起，单笔交易佣金不满5元按5元收取。
    commission = max(turnOver * rate, 5)

    return tax + transfer + commission

########################################################################
class Account(object):
    """
    AShare帐号
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""

        self.capital = 100000       # 回测时的起始本金（默认10万）
        self.slippage = 0           # 回测时假设的滑点
        self._rate = 3/10000        # 回测时假设的佣金比例（适用于百分比佣金）
        self.size = 1               # 合约大小，默认为1    
        self.priceTick = 0          # 价格最小变动 
        
        self.limitOrderCount = 0                    # 限价单编号
        self.limitOrderDict = OrderedDict()         # 限价单字典
        self.workingLimitOrderDict = OrderedDict()  # 活动限价单字典，用于进行撮合用
        
        self.tradeCount = 0             # 成交编号
        self.tradeDict = OrderedDict()  # 成交字典
        
        self.logList = []               # 日志记录
        
        # 当前最新数据，用于模拟成交用
        self.tick = None
        self.bar = None
        self.dt = None      # 最新的时间
        self._BTestId = ""

