from backtesting import Strategy


class XABCD(Strategy):
    TPSLRatio = 2
    sl_pct = 0.01
    tx_size = 0.99

    def sig1(self):
        return self.data.harmonic

    def init(self):
        super().init()
        self.signal = self.sig1

    def next(self):
        super().next()
        index = len(self.data) - 1

        for trade in self.trades:
            if trade.is_long:
                trade.sl = max(trade.sl, self.data.Close[index] * (1 - self.sl_pct))
            if trade.is_short:
                trade.sl = min(trade.sl, self.data.Close[index] * (1 + self.sl_pct))

        if self.signal != 0 and self.data.harmonic == 1 and not self.position.is_long:
            self.position.close()
            sl1 = self.data.Close[-1] - self.data.Close[-1] * self.sl_pct
            sldiff = abs(sl1 - self.data.Close[index])
            tp1 = self.data.Close[-1] + sldiff * self.TPSLRatio
            self.buy(sl=sl1, tp=tp1, size=self.tx_size)
            self.buy(sl=sl1, size=self.tx_size)

        elif (
            self.signal != 0 and self.data.harmonic == -1 and not self.position.is_short
        ):
            self.position.close()
            sl1 = self.data.Close[index] + self.data.Close[index] * self.sl_pct
            sldiff = abs(sl1 - self.data.Close[index])
            tp1 = self.data.Close[index] - sldiff * self.TPSLRatio
            self.sell(sl=sl1, tp=tp1, size=self.tx_size)
            self.sell(sl=sl1, size=self.tx_size)
