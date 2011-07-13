
from httplib2 import Http
import json
from urlparse import urlunparse
from urllib import urlencode

class ServerError(Exception):
    def __init__(self, ret):
        self.ret = ret
    def __str__(self):
        return "Server error: %s" % self.ret

class UserError(Exception):
    def __init__(self, errmsg):
        self.errmsg = errmsg
    def __str__(self):
        return self.errmsg

class MTGox:
    """MTGox API"""
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.server = "mtgox.com"
        self.timeout = 10
        self.actions = {"_get_ticker": ("GET", "VALID", "/code/data/ticker.php"),
                        "get_depth": ("GET", "VALID", "/code/data/getDepth.php"),
                        "get_trades": ("GET", "VALID", "/code/data/getTrades.php"),
                        "get_balance": ("POST", "VALID", "/code/getFunds.php"),
                        "buy_btc": ("POST", "VALID", "/code/buyBTC.php"),
                        "sell_btc": ("POST", "VALID", "/code/sellBTC.php"),
                        "_get_orders": ("POST", "VALID", "/code/getOrders.php"),
                        "_cancel_order": ("POST", "VALID", "/code/cancelOrder.php"),
                        "_withdraw": ("POST", "VALID", "/code/withdraw.php")}
        
        for action, (method, ssl, _) in self.actions.items():
            def _handler(action=action, **args):
                return self._request(action, method=method, ssl=ssl, args=args)
            setattr(self, action, _handler)

    def get_ticker(self):
        return self._get_ticker()["ticker"]

    def get_orders(self):
        return self._get_orders()["orders"] # can also return balance

    def cancel_order(self, oid, typ=None):
        orders = self.get_orders()
        if typ is None:
            order = [o for o in orders if o["oid"] == oid]
            if order:
                typ = order[0]["type"]
            else:
                raise UserError("unknown order/type")
        return self._cancel_order(oid=oid, type=typ)


    def withdraw(self, amount, btca, group1="BTC"):
        return self._withdraw(amount=amount, btca=btca, group1=group1)["status"] # can also return balance

    def _request(self, action, method="GET", ssl="VALID", args={}):
        query = args.copy()
        data = None
        headers = {}
        if method == "GET":
            url = self._url(action)
        if method == "POST":
            url = self._url(action, scheme="https")
            query["name"] = self.user
            query["pass"] = self.password
            data = urlencode(query)
            headers['Content-type'] = 'application/x-www-form-urlencoded'
        if ssl == "VALID":
            h = Http(cache=None, timeout=self.timeout)
        if ssl == "INVALID":
            h = Http(cache=None, timeout=self.timeout, disable_ssl_certificate_validation=True)


        try:
            #print "%s %s\n> |%s|" % (method, url, data)
            resp, content = h.request(url, method, headers=headers, body=data)
            #print "< %s (%s)" % (content, resp)
            if resp.status == 200:
                data = json.loads(content)
                if "error" in data:
                    raise UserError(data["error"])
                else:
                    return data 
            else:
                raise ServerError(content)
        except AttributeError, e: # 'NoneType' object has no attribute 'makefile'
            raise ServerError("timeout/refused")
        except ValueError, e:
            raise ServerError("%s: %s" % (e, content))

    def _url(self, action, scheme="http", args={}):
        url = urlunparse((scheme,
                          self.server,
                          self.actions[action][1], # path
                          '',
                          urlencode(args),
                          ''))
        return url

class ExchB(MTGox):
    def __init__(self,user,password):
	MTGox.__init__(self,user,password) 
        self.server = "www.exchangebitcoins.com"
        self.actions = {"_get_ticker": ("GET", "VALID", "/data/ticker"),
                        "get_depth": ("GET", "VALID", "/data/depth"),
                        "get_trades": ("GET", "VALID", "/data/recent"),
                        "get_balance": ("POST", "VALID", "/data/getFunds"),
                        "buy_btc": ("POST", "VALID", "/data/buyBTC"),
                        "sell_btc": ("POST", "VALID", "/data/sellBTC"),
                        "_get_orders": ("POST", "VALID", "/data/getOrders"),
                        "_cancel_order": ("POST", "VALID", "/data/cancelOrder")}


class TradeHill(MTGox):
    def __init__(self,user,password):
	MTGox.__init__(self,user,password)
        self.server = "api.tradehill.com"
        self.actions = {"_get_ticker": ("GET", "INVALID", "/APIv1/USD/Ticker",),
                        "get_depth": ("GET", "INVALID" "/APIv1/USD/Orderbook",),
                        "get_trades": ("GET", "INVALID", "/APIv1/USD/Trades"),
                        "get_balance": ("POST", "INVALID", "/APIv1/USD/GetBalance"),
                        "buy_btc": ("POST", "INVALID", "/APIv1/USD/BuyBTC"),
                        "sell_btc": ("POST", "INVALID", "/APIv1/USD/SellBTC"),
                        "_get_orders": ("POST", "INVALID", "/APIv1/USD/GetOrders"),
                        "_cancel_order": ("POST", "INVALID", "/APIv1/USD/CancelOrder")}
	

