# encoding: UTF-8

"""
展示如何执行策略回测。
"""
from __future__ import division
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME
import vnpy.trader.app.ctaStrategy.strategy as tg
import os
import gc
from time import sleep

#----------------------------------------------------------------------
def backTestSymbol(symbol, startDate):
    """将Multicharts导出的csv格式的历史数据插入到Mongo数据库中"""
    from vnpy.trader.app.ctaStrategy.strategy.strategyKingKeltner import KkStrategy
    from vnpy.trader.app.ctaStrategy.strategy.strategyBollChannel import BollChannelStrategy

    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置产品相关参数
    engine.setSlippage(0.2)     # 股指1跳
    engine.setRate(0.3/10000)   # 万0.3
    engine.setSize(100)         # 股指合约大小 
    engine.setPriceTick(0.2)    # 股指最小价格变动
    
    # 设置回测用的数据起始日期
    engine.setStartDate(startDate)
    engine.setDatabase(MINUTE_DB_NAME, symbol)
    
    # 在引擎中创建策略对象
    d = {}
    strategyList = [BollChannelStrategy, KkStrategy]
    engine.batchBacktesting(strategyList, d)

#----------------------------------------------------------------------
def backTestSymbolByAllStategy(symbol, startDate):

    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置产品相关参数
    engine.setSlippage(0.2)     # 股指1跳
    engine.setRate(0.3/10000)   # 万0.3
    engine.setSize(100)         # 股指合约大小 
    engine.setPriceTick(0.2)    # 股指最小价格变动
    
    # 设置回测用的数据起始日期
    engine.setStartDate(startDate)
    engine.setDatabase(MINUTE_DB_NAME, symbol)
    
    # 在引擎中创建策略对象
    strategyList = []
    for k in tg.STRATEGY_CLASS :
        strategyList.append(tg.STRATEGY_CLASS[k])

    d = {}
    engine.batchBacktesting(strategyList, d)

#----------------------------------------------------------------------

if __name__ == '__main__':

    backTestSymbolByAllStategy('IF0000', '20120101')
