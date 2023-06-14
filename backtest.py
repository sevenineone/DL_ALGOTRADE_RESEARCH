from enum import Enum
import pandas as pd
import plotly.graph_objects as go
        

class MLBackTrader():
    def __init__(self) -> None:
        self.pos = Enum("pos", ["LONG", "HOLD", "SHORT"])
        self.position = self.pos.HOLD
        self.target = None
        self.predicted = None
        self.current_portfolio = 1000
        self.portfolio = [self.current_portfolio]
        self.portfolio_time = [0]
        
        self.order_time = []
        self.order_price = []
        self.order_side = []
        self.open_price = 0
        self.open_portfolio = 0
        self.trade_profits = []
        
        self.maker_fee_multiplier = 0.0002
        self.taker_fee_multiplier = 0.0004
        self.spread_dummy = 0.01
        self.reg = None
        self.threshold = 0
        self.open_threshold = 1.8
        self.order_amount = 0.5
        
        
    def load_target(self, data):
        self.target = data
        
    def load_predicted(self, data):
        self.predicted = data
        
    def open(self, pos, price, time):
        self.open_portfolio = self.current_portfolio
        if pos == "long":
            print(f"|{time}|\n|OPEND \033[92mLONG\033[0m POSITION | {price}")
            amount = self.order_amount * (price + self.spread_dummy) * (1 + self.taker_fee_multiplier) 
            self.current_portfolio -= amount
        elif pos == "short":
            print(f"|{time}|\n|OPEND \033[91mSHORT\033[0m POSITION | {price}")
            amount = self.order_amount * (price - self.spread_dummy) * (1 - self.maker_fee_multiplier)
            self.current_portfolio += amount
        else:
            raise Exception("Long 0r short only!")
        ###########################################################
        self.open_price = price 
        self.order_time.append(time)
        self.order_price.append(price)
        self.order_side.append(pos)
    
    
    def close(self, pos, price, time):
        if pos == "long":
            amount = self.order_amount * (price - self.spread_dummy) * (1 - self.maker_fee_multiplier) 
            self.current_portfolio += amount
            print(f"|CLOSE \033[92mLONG\033[0m POSITION | {price} | profit: {(self.current_portfolio - self.open_portfolio):.5}")
            print("======================")
        elif pos == "short":
            amount = self.order_amount * (price + self.spread_dummy) * (1 + self.taker_fee_multiplier)
            self.current_portfolio -= amount
            print(f"|CLOSE \033[91mSHORT\033[0m POSITION | {price} | profit: {(self.current_portfolio - self.open_portfolio):.5}")
            print("======================")
        else:
            raise Exception("Long 0r short only!")
        ############################################################
        self.order_time += [time, time]
        self.order_price += [price, None]
        self.order_side += [pos, pos]
        
        self.trade_profits.append(self.current_portfolio - self.open_portfolio)
        self.portfolio.append(self.current_portfolio)
        self.portfolio_time.append(time)
        
    def get_orders_data(self):
          return pd.DataFrame({
            "time" : self.order_time,
            "price" : self.order_price,
            "side" : self.order_side
        })  
    
    def plot(self): 
        orders = self.get_orders_data()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
                                 y=self.target,
                                 mode='lines',
                                 name='price',
                                 line=dict(color='blue', width = 2)
                                 ))
        fig.add_trace(go.Scatter(x=orders[orders["side"] == "long"]["time"], 
                                 y=orders[orders["side"] == "long"]["price"],
                                 mode='lines+markers',
                                 name='long',
                                 line=dict(color='green', width = 1.5)
                                 ))
        fig.add_trace(go.Scatter(x=orders[orders["side"] == "short"]["time"], 
                                 y=orders[orders["side"] == "short"]["price"],
                                 mode='lines+markers',
                                 name='short',
                                 line=dict(color='red', width = 1.5)
                                 ))
        fig.show()

        
    def run(self):
        for i in range(0, len(self.target)-1):
            delta = self.predicted[i] - self.target[i]
            if self.position == self.pos.LONG:
                if abs(delta) < self.threshold or delta < 0 or self.target[i] <= self.open_price:
                    self.position = self.pos.HOLD
                    self.close("long", self.target[i], i)
            
            if self.position == self.pos.SHORT:
                if abs(delta) < self.threshold or delta > 0 or self.target[i] >= self.open_price:
                    self.position = self.pos.HOLD
                    self.close("short", self.target[i], i)
            
            if self.position == self.pos.HOLD:
                if delta > 0 and abs(delta) > self.open_threshold:
                    self.position = self.pos.LONG
                    self.open("long", self.target[i], i)
                elif delta < 0 and abs(delta) > self.open_threshold:
                    self.position = self.pos.SHORT
                    self.open("short", self.target[i], i)