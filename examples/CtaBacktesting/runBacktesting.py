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

hs300s= [
        "600000","600008","600009","600010","600011","600015","600016","600018","600019","600023",
        "600025","600028","600029","600030","600031","600036","600038","600048","600050","600061",
        "600066","600068","600085","600089","600100","600104","600109","600111","600115","600118",
        "600153","600157","600170","600176","600177","600188","600196","600208","600219","600221",
        "600233","600271","600276","600297","600309","600332","600339","600340","600346","600352",
        "600362","600369","600372","600373","600376","600383","600390","600398","600406","600415",
        "600436","600438","600482","600487","600489","600498","600516","600518","600519","600522",
        "600535","600547","600549","600570","600583","600585","600588","600606","600637","600660",
        "600663","600674","600682","600688","600690","600703","600704","600705","600739","600741",
        "600795","600804","600809","600816","600820","600837","600867","600886","600887","600893",
        "600900","600909","600919","600926","600958","600959","600977","600999","601006","601009",
        "601012","601018","601021","601088","601099","601108","601111","601117","601155","601166",
        "601169","601186","601198","601211","601212","601216","601225","601228","601229","601238",
        "601288","601318","601328","601333","601336","601360","601377","601390","601398","601555",
        "601600","601601","601607","601611","601618","601628","601633","601668","601669","601688",
        "601718","601727","601766","601788","601800","601808","601818","601828","601838","601857",
        "601866","601877","601878","601881","601888","601898","601899","601901","601919","601933",
        "601939","601958","601985","601988","601989","601991","601992","601997","601998","603160",
        "603260","603288","603799","603833","603858","603993","000001","000002","000060","000063",
        "000069","000100","000157","000166","000333","000338","000402","000413","000415","000423",
        "000425","000503","000538","000540","000559","000568","000623","000625","000627","000630",
        "000651","000671","000709","000723","000725","000728","000768","000776","000783","000786",
        "000792","000826","000839","000858","000876","000895","000898","000938","000959","000961",
        "000963","000983","001965","001979","002007","002008","002024","002027","002044","002050",
        "002065","002074","002081","002085","002142","002146","002153","002202","002230","002236",
        "002241","002252","002294","002304","002310","002352","002385","002411","002415","002450",
        "002456","002460","002466","002468","002470","002475","002493","002500","002508","002555",
        "002558","002572","002594","002601","002602","002608","002624","002625","002673","002714",
        "002736","002739","002797","002925","300003","300015","300017","300024","300027","300033",
        "300059","300070","300072","300122","300124","300136","300144","300251","300408","300433"
        ]

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
    # engine.initStrategy(KkStrategy, d)
    
    # # 开始跑回测
    # engine.runBacktesting()
    
    # # 显示回测结果
    # engine.showBacktestingResult()

#----------------------------------------------------------------------
def backTestSymbolByStategy(symbol, stategy, startDate):
    """将Multicharts导出的csv格式的历史数据插入到Mongo数据库中"""

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
    engine.initStrategy(stategy, d)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()

    engine.clearBacktestingResult()

# symbols= ["601000", "601001", "601002", "601003", "601005", "601006", "601007", "601008", "601009", "601010", "601011", "601012", "601018", "601028", "601038", "601058", "601088", "601098", "601099", "601100", "601101", "601106", "601107", "601111", "601113", "601116", "601117", "601118", "601126", "601137", "601139", "601158", "601166", "601168", "601169", "601177", "601179", "601186", "601188", "601199", "601208", "601216", "601218", "601222", "601231", "601233", "601238", "601258", "601268", "601288", "601299", "601311", "601313", "601318", "601328", "601333", "601336", "601339", "601369", "601377", "601388", "601390", "601398", "601515", "601518", "601555", "601558", "601566", "601567", "601588", "601599", "601600", "601601", "601607", "601608", "601616", "601618", "601628", "601633", "601636", "601666", "601668", "601669", "601677", "601678", "601688", "601699", "601700", "601717", "601718", "601727", "601766", "601777", "601788", "601789", "601798", "601799", "601800", "601801", "601808", "601818", "601857", "601866", "601872", "601877", "601880", "601886", "601888", "601890", "601898", "601899", "601901", "601908", "601918", "601919", "601928", "601929", "601933", "601939", "601958", "601965", "601988", "601989", "601991", "601992", "601996", "601998", "601999"]
# symbols= ["601188", "601199", "601208", "601216", "601218", "601222", "601231", "601233", "601238", "601258", "601268", "601288", "601299", "601311", "601313", "601318", "601328", "601333", "601336", "601339", "601369", "601377", "601388", "601390", "601398", "601515", "601518", "601555", "601558", "601566", "601567", "601588", "601599", "601600", "601601", "601607", "601608", "601616", "601618", "601628", "601633", "601636", "601666", "601668", "601669", "601677", "601678", "601688", "601699", "601700", "601717", "601718", "601727", "601766", "601777", "601788", "601789", "601798", "601799", "601800", "601801", "601808", "601818", "601857", "601866", "601872", "601877", "601880", "601886", "601888", "601890", "601898", "601899", "601901", "601908", "601918", "601919", "601928", "601929", "601933", "601939", "601958", "601965", "601988", "601989", "601991", "601992", "601996", "601998", "601999"]
symbols= ["601000"]
stoppedChilds = len(symbols)

#----------------------------------------------------------------------
def backTestSymbolByAllStategy(symbol, startDate):
    for k in tg.STRATEGY_CLASS :
        backTestSymbolByStategy(symbol, tg.STRATEGY_CLASS[k], startDate)

if __name__ == '__main__':

    backTestSymbol('A601000', '20110101')
    exit()
    
    # backTestSymbol('IF0000', '20120101');

    # 设置回测用的数据起始日期
    for s in symbols :
        try:
            gc.collect()
            backTestSymbolByAllStategy('A'+s, '20110101')
        except OSError, e:
            pass

        # try:
        #     if os.fork() ==0 : # child process
        #         print "this is child process of "+s
        #         stoppedChilds = stoppedChilds -1
        #         try :
        #             backTestSymbolByAllStategy('A'+s, '20110101')
        #         except:
        #             pass
        #         stoppedChilds = stoppedChilds +1
        #     else: # this process as the parent
        #         print "this is parent process."
        #         sleep(10)
        #         while stoppedChilds < len(symbols) :
        #             sleep(3)
        #         print "parent process done"
        #         pass
        # except OSError, e:
        #     pass
