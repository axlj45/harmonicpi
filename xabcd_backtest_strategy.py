from backtesting import Strategy
import math

class XABCD(Strategy):
    TPSLRatio = 2
    sl_pct = 0.025
    tx_size = 0.5

    def sig1(self):
        return self.data.harmonic[-2]

    def init(self):
        super().init()
        self.signal = self.sig1

    def next(self):
        super().next()
        if self.signal() == 0:
            return

        index = len(self.data) - 2

        x = self.data.x[index]
        a = self.data.a[index]
        d = self.data.d[index]
        tppc = abs((a["close"] - x["close"]) * 0.35)

        for trade in self.trades:
            newSl = trade.sl
            if trade.is_long and trade.tp is None:
                newSl = max(trade.sl, self.data.Close[0] * (1 - self.sl_pct))
            if trade.is_short and trade.tp is None:
                newSl = min(trade.sl, self.data.Close[0] * (1 + self.sl_pct))
            if newSl != trade.sl:
                # print(trade.sl, newSl, trade.tp)
                trade.sl = newSl

        if self.signal() == 1 and not self.position.is_long:
            self.position.close()
            sl1 = self.data.Close[-1] - self.data.Close[-1] * self.sl_pct
            tp1 = d["close"] + tppc
            if tp1 > sl1 and tp1 > self.data.Close[-1] and sl1 < self.data.Close[-1]:
                full_size = self.equity/self.data.Close[0]
                half_size = math.floor(full_size/2)
                self.buy(sl=sl1, tp=tp1, size=self.tx_size)
                self.buy(sl=sl1, size=self.tx_size)

        elif self.signal() == -1 and not self.position.is_short:
            self.position.close()
            sl1 = self.data.Close[-1] + self.data.Close[-1] * self.sl_pct
            tp1 = d["close"] - tppc
            if tp1 < sl1 and tp1 < self.data.Close[-1] and sl1 > self.data.Close[-1]:
                full_size = self.equity/self.data.Close[0]
                half_size = math.floor(full_size/2)
                self.sell(sl=sl1, tp=tp1, size=self.tx_size)
                self.sell(sl=sl1, size=self.tx_size)

        # for trade in self.trades:
        #     if trade.is_long:
        #         trade.sl = max(trade.sl, self.data.Close[-1] * (1 - self.sl_pct))
        #     if trade.is_short:
        #         trade.sl = min(trade.sl, self.data.Close[-1] * (1 + self.sl_pct))
