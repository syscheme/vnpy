# encoding: utf-8

import urllib
import hmac
import base64
import hashlib
import requests 
import traceback
from copy import copy
from datetime import datetime
from threading import Thread
from Queue import Queue, Empty
from multiprocessing.dummy import Pool
from time import sleep

import json
import zlib
from websocket import create_connection, _exceptions # retrieve package: sudo pip install websocket-client pathlib

# 常量定义
TIMEOUT = 5
HUOBI_API_HOST = "api.huobi.pro"
HADAX_API_HOST = "api.hadax.com"
LANG = 'zh-CN'

DEFAULT_GET_HEADERS = {
    "Content-type": "application/x-www-form-urlencoded",
    'Accept': 'application/json',
    'Accept-Language': LANG,
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
}

DEFAULT_POST_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Language': LANG,
    'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'    
}


#----------------------------------------------------------------------
def createSign(params, method, host, path, secretKey):
    """创建签名"""
    sortedParams = sorted(params.items(), key=lambda d: d[0], reverse=False)
    encodeParams = urllib.urlencode(sortedParams)
    
    payload = [method, host, path, encodeParams]
    payload = '\n'.join(payload)
    payload = payload.encode(encoding='UTF8')

    secretKey = secretKey.encode(encoding='UTF8')

    digest = hmac.new(secretKey, payload, digestmod=hashlib.sha256).digest()

    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature    


########################################################################
class TradeApi(object):
    """交易API"""
    HUOBI = 'huobi'
    HADAX = 'hadax'
    
    SYNC_MODE = 'sync'
    ASYNC_MODE = 'async'

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.accessKey = ''
        self.secretKey = ''
    
        self.mode = self.ASYNC_MODE
        self.active = False         # API工作状态   
        self.reqid = 0              # 请求编号
        self.queue = Queue()        # 请求队列
        self.pool = None            # 线程池
        
    #----------------------------------------------------------------------
    def init(self, host, accessKey, secretKey, mode=None):
        """初始化"""
        if host == self.HUOBI:
            self.hostname = HUOBI_API_HOST
        else:
            self.hostname = HADAX_API_HOST
        self.hosturl = 'https://%s' %self.hostname
            
        self.accessKey = accessKey
        self.secretKey = secretKey
        
        if mode:
            self.mode = mode
            
        self.proxies = {
#              "http"  : "http://localhost:8118/", 
#              "https" : "http://localhost:8118/"
        }
    
        return True
        
    #----------------------------------------------------------------------
    def start(self, n=10):
        """启动"""
        self.active = True
        
        if self.mode == self.ASYNC_MODE:
            self.pool = Pool(n)
            self.pool.map_async(self.run, range(n))
        
    #----------------------------------------------------------------------
    def close(self):
        """停止"""
        self.active = False
        self.pool.close()
        self.pool.join()
        
    #----------------------------------------------------------------------
    def httpGet(self, url, params):
        """HTTP GET"""        
        headers = copy(DEFAULT_GET_HEADERS)
        postdata = urllib.urlencode(params)
        
        try:
            response = requests.get(url, postdata, headers=headers, proxies=self.proxies, timeout=TIMEOUT)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, u'GET请求失败，状态代码：%s' %response.status_code
        except Exception as e:
            return False, u'GET请求触发异常，原因：%s' %e
    
    #----------------------------------------------------------------------    
    def httpPost(self, url, params, add_to_headers=None):
        """HTTP POST"""       
        headers = copy(DEFAULT_POST_HEADERS)
        postdata = json.dumps(params)
        
        try:
            response = requests.post(url, postdata, headers=headers, proxies=self.proxies, timeout=TIMEOUT)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, u'POST请求失败，返回信息：%s' %response.json()
        except Exception as e:
            return False, u'POST请求触发异常，原因：%s' %e
        
    #----------------------------------------------------------------------
    def generateSignParams(self):
        """生成签名参数"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        d = {
            'AccessKeyId': self.accessKey,
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'Timestamp': timestamp
        }    
        
        return d
        
    #----------------------------------------------------------------------
    def apiGet(self, path, params):
        """API GET"""
        method = 'GET'
        
        params.update(self.generateSignParams())
        params['Signature'] = createSign(params, method, self.hostname, path, self.secretKey)
        
        url = self.hosturl + path
        #print("url=%s, param:%s" % (url, params))
        
        return self.httpGet(url, params)
    
    #----------------------------------------------------------------------
    def apiPost(self, path, params):
        """API POST"""
        method = 'POST'
        
        signParams = self.generateSignParams()
        signParams['Signature'] = createSign(signParams, method, self.hostname, path, self.secretKey)
        
        url = self.hosturl + path + '?' + urllib.urlencode(signParams)

        return self.httpPost(url, params)
    
    #----------------------------------------------------------------------
    def addReq(self, path, params, func, callback):
        """添加请求"""       
        # 异步模式
        if self.mode == self.ASYNC_MODE:
            self.reqid += 1
            req = (path, params, func, callback, self.reqid)
            self.queue.put(req)
            return self.reqid
        # 同步模式
        else:
            return func(path, params)
    
    #----------------------------------------------------------------------
    def processReq(self, req):
        """处理请求"""
        path, params, func, callback, reqid = req
        result, data = func(path, params)
        
        if result:
            if data['status'] == 'ok':
                callback(data['data'], reqid)
            else:
                msg = u'错误代码：%s，错误信息：%s' %(data['err-code'], data['err-msg'])
                self.onError(msg, reqid)
        else:
            self.onError(data, reqid)
            
            # 失败的请求重新放回队列，等待下次处理
            self.queue.put(req)
    
    #----------------------------------------------------------------------
    def run(self, n):
        """连续运行"""
        while self.active:    
            try:
                req = self.queue.get(timeout=1)
                self.processReq(req)
            except Empty:
                pass
    
    #----------------------------------------------------------------------
    def getSymbols(self):
        """查询合约代码"""
        if self.hostname == HUOBI_API_HOST:
            path = '/v1/common/symbols'
        else:
            path = '/v1/hadax/common/symbols'

        params = {}
        func = self.apiGet
        callback = self.onGetSymbols
        
        return self.addReq(path, params, func, callback)
    
    #----------------------------------------------------------------------
    def getCurrencys(self):
        """查询支持货币"""
        if self.hostname == HUOBI_API_HOST:
            path = '/v1/common/currencys'
        else:
            path = '/v1/hadax/common/currencys'

        params = {}
        func = self.apiGet
        callback = self.onGetCurrencys
        
        return self.addReq(path, params, func, callback)   
    
    #----------------------------------------------------------------------
    def getTimestamp(self):
        """查询系统时间"""
        path = '/v1/common/timestamp'
        params = {}
        func = self.apiGet
        callback = self.onGetTimestamp
        
        return self.addReq(path, params, func, callback) 
    
    #----------------------------------------------------------------------
    def getAccounts(self):
        """查询账户"""
        path = '/v1/account/accounts'
        params = {}
        func = self.apiGet
        callback = self.onGetAccounts
    
        return self.addReq(path, params, func, callback)         
    
    #----------------------------------------------------------------------
    def getAccountBalance(self, accountid):
        """查询余额"""
        if self.hostname == HUOBI_API_HOST:
            path = '/v1/account/accounts/%s/balance' %accountid
        else:
            path = '/v1/hadax/account/accounts/%s/balance' %accountid
            
        params = {}
        func = self.apiGet
        callback = self.onGetAccountBalance
    
        return self.addReq(path, params, func, callback) 
    
    #----------------------------------------------------------------------
    def getOrders(self, symbol, states, types=None, startDate=None, 
                  endDate=None, from_=None, direct=None, size=None):
        """查询委托"""
        path = '/v1/order/orders'
        
        params = {
            'symbol': symbol,
            'states': states
        }
        
        if types:
            params['types'] = types
        if startDate:
            params['start-date'] = startDate
        if endDate:
            params['end-date'] = endDate        
        if from_:
            params['from'] = from_
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size        
    
        func = self.apiGet
        callback = self.onGetOrders
    
        return self.addReq(path, params, func, callback)     

    #----------------------------------------------------------------------
    def getOpenOrders(self, accountId=None, symbol=None, side=None, size=None):
        """查询当前帐号下未成交订单
            “account_id” 和 “symbol” 需同时指定或者二者都不指定。如果二者都不指定，返回最多500条尚未成交订单，按订单号降序排列。
        """
        path = '/v1/order/openOrders'
        
        params = { # initial with default required params
            #'account_id': accountId,
            #'symbol': symbol,
        }
        
        if symbol:
            params['symbol'] = symbol
            params['account_id'] = accountId

        if side:
            params['side'] = side

        if size:
            params['size'] = size        
    
        func = self.apiGet
        callback = self.onGetOrders
    
        return self.addReq(path, params, func, callback)     
    
    #----------------------------------------------------------------------
    def getMatchResults(self, symbol, types=None, startDate=None, 
                  endDate=None, from_=None, direct=None, size=None):
        """查询委托"""
        path = '/v1/order/matchresults'

        params = {
            'symbol': symbol
        }

        if types:
            params['types'] = types
        if startDate:
            params['start-date'] = startDate
        if endDate:
            params['end-date'] = endDate        
        if from_:
            params['from'] = from_
        if direct:
            params['direct'] = direct
        if size:
            params['size'] = size        

        func = self.apiGet
        callback = self.onGetMatchResults

        return self.addReq(path, params, func, callback)   
    
    #----------------------------------------------------------------------
    def getOrder(self, orderid):
        """查询某一委托"""
        path = '/v1/order/orders/%s' %orderid
    
        params = {}
    
        func = self.apiGet
        callback = self.onGetOrder
    
        return self.addReq(path, params, func, callback)             
    
    #----------------------------------------------------------------------
    def getMatchResult(self, orderid):
        """查询某一委托"""
        path = '/v1/order/orders/%s/matchresults' %orderid
    
        params = {}
    
        func = self.apiGet
        callback = self.onGetMatchResult
    
        return self.addReq(path, params, func, callback)     
    
    #----------------------------------------------------------------------
    def placeOrder(self, accountid, amount, symbol, type_, price=None, source=None):
        """下单"""
        if self.hostname == HUOBI_API_HOST:
            path = '/v1/order/orders/place'
        else:
            path = '/v1/hadax/order/orders/place'
        
        params = {
            'account-id': accountid,
            'amount': amount,
            'symbol': symbol,
            'type': type_
        }
        
        if price:
            params['price'] = price
        if source:
            params['source'] = source     

        func = self.apiPost
        callback = self.onPlaceOrder

        return self.addReq(path, params, func, callback)           
    
    #----------------------------------------------------------------------
    def cancelOrder(self, orderid):
        """撤单"""
        path = '/v1/order/orders/%s/submitcancel' %orderid
        
        params = {}
        
        func = self.apiPost
        callback = self.onCancelOrder

        return self.addReq(path, params, func, callback)          
    
    #----------------------------------------------------------------------
    def batchCancel(self, orderids):
        """批量撤单"""
        path = '/v1/order/orders/batchcancel'
    
        params = {
            'order-ids': orderids
        }
    
        func = self.apiPost
        callback = self.onBatchCancel
    
        return self.addReq(path, params, func, callback)     
        
    #----------------------------------------------------------------------
    def onError(self, msg, reqid):
        """错误回调"""
        print(msg, reqid)
        
    #----------------------------------------------------------------------
    def onGetSymbols(self, data, reqid):
        """查询代码回调"""
        #print reqid, data 
        for d in data:
            print(d)
    
    #----------------------------------------------------------------------
    def onGetCurrencys(self, data, reqid):
        """查询货币回调"""
        print (reqid, data)
    
    #----------------------------------------------------------------------
    def onGetTimestamp(self, data, reqid):
        """查询时间回调"""
        print (reqid, data)
        
    #----------------------------------------------------------------------
    def onGetAccounts(self, data, reqid):
        """查询账户回调"""
        print (reqid, data)
    
    #----------------------------------------------------------------------
    def onGetAccountBalance(self, data, reqid):
        """查询余额回调"""
        print (reqid, data)
        for d in data['data']['list']:
            print (d)
        
    #----------------------------------------------------------------------
    def onGetOrders(self, data, reqid):
        """查询委托回调"""
        print (reqid, data)
        
    #----------------------------------------------------------------------
    def onGetMatchResults(self, data, reqid):
        """查询成交回调"""
        print (reqid, data)
        
    #----------------------------------------------------------------------
    def onGetOrder(self, data, reqid):
        """查询单一委托回调"""
        print (reqid, data)
        
    #----------------------------------------------------------------------
    def onGetMatchResult(self, data, reqid):
        """查询单一成交回调"""
        print (reqid, data)
        
    #----------------------------------------------------------------------
    def onPlaceOrder(self, data, reqid):
        """委托回调"""
        print (reqid, data)
    
    #----------------------------------------------------------------------
    def onCancelOrder(self, data, reqid):
        """撤单回调"""
        print (reqid, data)
        
    #----------------------------------------------------------------------
    def onBatchCancel(self, data, reqid):
        """批量撤单回调"""
        print (reqid, data)


########################################################################
class DataApi(object):
    """行情接口
    https://github.com/huobiapi/API_Docs/wiki/WS_request
    """
    HUOBI = 'huobi'
    HADAX = 'hadax'

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.ws = None
        self.url = ''
        
        self.reqid = 0
        self.active = False
        self.thread = Thread(target=self.run)
        
        self.subDict = {}
        
        self.url = ''
        self.proxies = {}
    
    #----------------------------------------------------------------------
    def init(self, exchHost, proxyHost=None, proxyPort=0):
        """初始化"""
        if exchHost == self.HUOBI:
            hostname = HUOBI_API_HOST
        else:
            hostname = HADAX_API_HOST
        self.url = 'wss://%s/ws' % hostname
            
        if proxyHost :
            self.proxyHost = proxyHost
            self.proxyPort = proxyPort

    #----------------------------------------------------------------------
    def run(self):
        """执行连接"""
        while self.active:
            try:
                stream = self.ws.recv()
                result = zlib.decompress(stream, 47).decode('utf-8')
                data = json.loads(result)
                self.onData(data)
            except zlib.error:
                self.onError(u'数据解压出错：%s' %stream)
            except:
                self.onError('行情服务器连接断开')
                result = self._doConnect()
                if not result:
                    self.onError(u'等待3秒后再次重连')
                    sleep(3)
                else:
                    self.onError(u'行情服务器重连成功')
                    self.resubscribe()
    
    #----------------------------------------------------------------------
    def _doConnect(self):
        """重连"""
        try:
            if self.proxyHost :
                self.ws = create_connection(self.url, http_proxy_host=self.proxyHost, http_proxy_port=self.proxyPort)
            else :
                self.ws = create_connection(self.url)

            self._resubscribe()

            return True

        except:
            msg = traceback.format_exc()
            self.onError(u'行情服务器重连失败：%s' %msg)            
            return False
        
    #----------------------------------------------------------------------
    def _resubscribe(self):
        """重新订阅"""
        d = self.subDict
        self.subDict = {}
        for topic in d.keys():
            self.subTopic(topic)
        
    #----------------------------------------------------------------------
    def connect(self):
        """连接"""
        if not self._doConnect() :
            return False
            
        self.active = True
        self.thread.start()
            
        return True
        
    #----------------------------------------------------------------------
    def close(self):
        """停止"""
        if self.active:
            self.active = False
            self.thread.join()
            self.ws.close()
        
    #----------------------------------------------------------------------
    def sendReq(self, req):
        """发送请求"""
        stream = json.dumps(req)
        self.ws.send(stream)            
        
    #----------------------------------------------------------------------
    def pong(self, data):
        """响应心跳"""
        req = {'pong': data['ping']}
        self.sendReq(req)
    
    #----------------------------------------------------------------------
    def subTopic(self, topic):
        """订阅主题"""
        if topic in self.subDict:
            return
        
        self.reqid += 1
        req = {
            'sub': topic,
            'id': str(self.reqid)
        }
        self.sendReq(req)
        
        self.subDict[topic] = str(self.reqid)
    
    #----------------------------------------------------------------------
    def unsubTopic(self, topic):
        """取消订阅主题"""
        if topic not in self.subDict:
            return
        req = {
            'unsub': topic,
            'id': self.subDict[topic]
        }
        self.sendReq(req)
        
        del self.subDict[topic]
    
    #----------------------------------------------------------------------
    def subscribeMarketDepth(self, symbol,step=0):
        """订阅行情深度"""
        topic = 'market.%s.depth.step%d' %(symbol, step%6) # allowed step 0~5
        self.subTopic(topic)
        
    #----------------------------------------------------------------------
    def subscribeTradeDetail(self, symbol):
        """订阅成交细节"""
        topic = 'market.%s.trade.detail' %symbol
        self.subTopic(topic)
        
    #----------------------------------------------------------------------
    def subscribeMarketDetail(self, symbol):
        """订阅市场细节"""
        topic = 'market.%s.detail' %symbol
        self.subTopic(topic)
        
    #----------------------------------------------------------------------
    def subscribeKline(self, symbol,minutes=1):
        """订阅K线数据"""
        period ="1min"
        minutes /=5
        if minutes >0:
            period ="5min"

        minutes /=3
        if minutes >0:
            period ="15min"

        minutes /=2
        if minutes >0:
            period ="30min"

        minutes /=2
        if minutes >0:
            period ="60min"

        minutes /=4
        if minutes >0:
            period ="4hour"

        minutes /=6
        if minutes >0:
            period ="1day"

        minutes /=7
        if minutes >0:
            period ="1week"

        minutes /=4
        if minutes >0:
            period ="1mon"

        minutes /=12
        if minutes >0:
            period ="1year"

        topic = 'market.%s.kline.%s' %(symbol, period) # allowed { 1min, 5min, 15min, 30min, 60min, 4hour,1day, 1mon, 1week, 1year }
        self.subTopic(topic)
        
    #----------------------------------------------------------------------
    def onError(self, msg):
        """错误推送"""
        print (msg)
        
    #----------------------------------------------------------------------
    def onData(self, data):
        """数据推送"""
        if 'ping' in data:
            self.pong(data)
        elif 'ch' in data:
            if 'depth.step' in data['ch']:
                self.onMarketDepth(data)
            elif 'kline' in data['ch']:
                self.onKline(data)
            elif 'trade.detail' in data['ch']:
                self.onTradeDetail(data)
            elif 'detail' in data['ch']:
                self.onMarketDetail(data)
        elif 'err-code' in data:
            self.onError(u'错误代码：%s, 信息：%s' %(data['err-code'], data['err-msg']))
    
    #----------------------------------------------------------------------
    def onMarketDepth(self, data):
        """行情深度推送 
        sample:
        {u'ch': u'market.ethusdt.depth.step0', u'ts': 1531119204038, u'tick': {	u'version': 11837097362, u'bids': [
            [481.2, 6.9387], [481.18, 1.901], [481.17, 5.0], [481.02, 0.96], [481.0, 4.9474], [480.94, 9.537], [480.93, 3.5159], [480.89, 1.0], [480.81, 2.06], [480.8, 30.2504], [480.72, 0.109], [480.64, 0.06], 		[480.63, 1.0], [480.61, 0.109], [480.6, 0.4899], [480.58, 1.9059], [480.56, 0.06], [480.5, 21.241], [480.49, 1.1444], [480.46, 1.0], [480.44, 2.4982], [480.43, 1.0], [480.41, 0.1875], [480.35, 1.0637], 		...		
            [494.01, 0.05], [494.05, 0.231], [494.26, 50.3659], [494.45, 0.2889]
        ]}}
        """
        print (data)
    
    #----------------------------------------------------------------------
    def onTradeDetail(self, data):
        """成交细节推送
        {u'tick': {u'data': [{u'price': 481.93, u'amount': 0.1499, u'direction': u'buy', u'ts': 1531119914439, u'id': 118378776467405480484L}, {u'price': 481.94, u'amount': 0.2475, u'direction': u'buy', u'ts': 1531119914439, u'id': 118378776467405466973L}, {u'price': 481.97, u'amount': 6.3635, u'direction': u'buy', u'ts': 1531119914439, u'id': 118378776467405475106L}, {u'price': 481.98, u'amount': 0.109, u'direction': u'buy', u'ts': 1531119914439, u'id': 118378776467405468495L}, {u'price': 481.98, u'amount': 0.109, u'direction': u'buy', u'ts': 1531119914439, u'id': 118378776467405468818L}, {u'price': 481.99, u'amount': 6.3844, u'direction': u'buy', u'ts': 1531119914439, u'id': 118378776467405471868L}, {u'price': 482.0, u'amount': 0.6367, u'direction': u'buy', u'ts': 1531119914439, u'id': 118378776467405439802L}], u'id': 11837877646, u'ts': 1531119914439}, u'ch': u'market.ethusdt.trade.detail', u'ts': 1531119914494}
        {u'tick': {u'data': [{u'price': 481.96, u'amount': 0.109, u'direction': u'sell', u'ts': 1531119918505, u'id': 118378822907405482834L}], u'id': 11837882290, u'ts': 1531119918505}, u'ch': u'market.ethusdt.trade.detail', u'ts': 1531119918651}
        """
        print (data)
    
    #----------------------------------------------------------------------
    def onMarketDetail(self, data):
        """市场细节推送, 最近24小时成交量、成交额、开盘价、收盘价、最高价、最低价、成交笔数等
        {u'tick': {u'count': 103831, u'vol': 39127093.56251132, u'high': 494.99, u'amount': 80614.73642133494, u'version': 11838075621, u'low': 478.0, u'close': 482.08, u'open': 484.56, u'id': 11838075621}, u'ch': u'market.ethusdt.detail', u'ts': 1531120097994}
        """
        print (data)

    #----------------------------------------------------------------------
    def onKline(self, data):
        """K线数据
        {u'tick': {u'count': 103831, u'vol': 39127093.56251132, u'high': 494.99, u'amount': 80614.73642133494, u'version': 11838075621, u'low': 478.0, u'close': 482.08, u'open': 484.56, u'id': 11838075621}, u'ch': u'market.ethusdt.detail', u'ts': 1531120097994}
        """
        print (data)
