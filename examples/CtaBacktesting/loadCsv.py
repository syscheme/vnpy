# encoding: UTF-8

"""
导入MC导出的CSV历史数据到MongoDB中
"""

from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME
import vnpy.trader.app.ctaStrategy.ctaHistoryData as hd


if __name__ == '__main__':
    #loadMcCsv('examples/CtaBacktesting/IF0000_1min.csv', MINUTE_DB_NAME, 'IF0000')
    # loadMcCsvBz2('examples/CtaBacktesting/IF0000_1min.csv.bz2', MINUTE_DB_NAME, 'IF0000')
    # loadMcCsv('rb0000_1min.csv', MINUTE_DB_NAME, 'rb0000')
    hd.loadTaobaoCsvBz2('/mnt/haswell-home/tmp/AShare1minCsv/2012.7-2012.12/SH601519.csv.bz2', MINUTE_DB_NAME, 'A601519')
    hd.loadTaobaoCsvBz2('/mnt/haswell-home/tmp/AShare1minCsv/2012.1-2012.6/SH601519.csv.bz2', MINUTE_DB_NAME, 'A601519')
    hd.loadTaobaoCsvBz2('/mnt/haswell-home/tmp/AShare1minCsv/2011.7-2011.12/SH601519.csv.bz2', MINUTE_DB_NAME, 'A601519')
    hd.loadTaobaoCsvBz2('/mnt/haswell-home/tmp/AShare1minCsv/2011.1-2011.6/SH601519.csv.bz2', MINUTE_DB_NAME, 'A601519')



