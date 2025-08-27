# 导入函数库
from jqdata import *
import math
import numpy as np
import pandas as pd
import functools
from jqfactor import get_factor_values
import statsmodels.api as sm

from datetime import datetime





# 初始化函数，设定基准等等
def initialize(context):
    # 设定恒生指数作为基准
    set_benchmark('000047.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    # log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    ### 股票相关设定 ###
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5),type='stock')
    g.index={
        'big':"000300.XSHG", #沪深300
        'small':'399006.XSHE', #创业板指
        "market":'000047.XSHG', #上证全指
    }
    g.etf={
        'big':"510300.XSHG", #300ETF
        'small':'159915.XSHE', #创业板ETF
    }
    g.res={
        'big':1,
        'small':1,
    }
    g.count=0
    g.portfolio_change=20
   
      # 开盘时运行
    run_daily(market_open, time='open')
      # 收盘后运行
    run_daily(after_market_close, time='after_close')
    
    
def get_signal(context):
    
    res={
        'big':0,
        'small':0,
    }
    
    df=get_price(list(g.index.values()),end_date=context.previous_date,count=1000,frequency='1d',fields=['close'],fq='pre')['close']
    
    df=df/df.shift(250)
    df.dropna(inplace=True)
    
    for index in df.columns: # 计算超额收益
        if index != g.index['market']:
            df[index]=df[index]-df[g.index['market']]+1
            
    #计算全盘是否暴跌
    
    mkt=df[g.index['market']]
    mkt=mkt.apply(lambda x : math.log(x,10))
    c,t =sm.tsa.filters.hpfilter(mkt,lamb=100000)
    
    T1=[]
    
    for pos in range(-20,0):
        X=list(np.arange(20))
        X=sm.add_constant(X)
        
        est=sm.OLS(t.iloc[pos-20:pos],X)
        est=est.fit()
        T1.append(est.params['x1'])
    X=list(np.arange(20))
    X=sm.add_constant(X)
    est1=sm.OLS(T1,X)
    est1=est1.fit()
    
    T2=est1.params[1]
    
    if T1[-1]<0 and T2<0:
        return res
    
    # 如果大盘没有暴跌
    
    df =df.drop(g.index['market'],1)
    for index in df.columns:  # 计算RS
        df[index]=df[index].apply(lambda x : math.log(x,10))
    
    diff= df[g.index['big']]-df[g.index['small']]
    
    cycle,trend=sm.tsa.filters.hpfilter(diff,lamb=100000)
    
    t1=[]
    
    for pos in range(-20,0):
        x=list(np.arange(20))
        x=sm.add_constant(x)
        
        est=sm.OLS(trend.iloc[pos-20:pos],x)
        est=est.fit()
        t1.append(est.params['x1'])
    x=list(np.arange(20))
    x=sm.add_constant(x)
    est1=sm.OLS(t1,x)
    est1=est1.fit()
    
    t2=est1.params[1]
    
    #通过1，2阶导分配大小盘资金
    
    if t1[-1]>0 and t2>0:
        res['big']=1
        res['small']=0
    if t1[-1]>0 and t2<0:
        res['big']=1
        res['small']=1
    if t1[-1]<0 and t2>0:
        res['big']=1
        res['small']=1
    if t1[-1]<0 and t2<0:
        res['big']=0
        res['small']=1
    
    return res
    
    

def allocate_cash(context,res):
    
    if res['big']==res['small']:
        order_target(g.etf['big'],0)
        order_target(g.etf['small'],0)
        if res['big']==1:
            cash = context.portfolio.available_cash*0.5
            order_value(g.etf['big'],cash)
            order_value(g.etf['small'],cash)
        
        
    else:
        if g.res['big']==1:
            order_target(g.etf['big'],0)
            order_value(g.etf['small'],context.portfolio.available_cash)
        else:
            order_target(g.etf['small'],0)
            order_value(g.etf['big'],context.portfolio.available_cash)
    
    g.res=res
    




## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    return
    
   
    
  
## 开盘时运行函数
def market_open(context):
    if g.count%g.portfolio_change==0:
        # log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
        res=get_signal(context)
        
        if g.res['big']!=res['big'] or g.res['small']!=res['small']:
            allocate_cash(context,res)  
    
        

def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
    
    

## 收盘后运行函数
def after_market_close(context):
    g.count=g.count+1
   
