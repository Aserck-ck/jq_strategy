import numpy as np
import pandas as pd


#初始化函数 
def initialize(context):
    # 设定基准
    set_benchmark('000001.XSHG')
    # 用真实价格交易
    set_option('use_real_price', True)
    # 打开防未来函数
    set_option("avoid_future_data", True)
    set_slippage(PriceRelatedSlippage(0.00246),type='stock')
    # 设置交易成本
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 过滤一定级别的日志
    log.set_level('system', 'error')
    # 参数
    g.etf_pool = [
        '518880.XSHG', #黄金ETF（大宗商品）
        '513100.XSHG', #纳指100（海外资产）
        '159915.XSHE', #创业板100（成长股，科技股，中小盘）
        '510180.XSHG', #上证180（价值股，蓝筹股，中大盘）
        '510650.XSHG', #金融行业
        '510660.XSHG', #医药行业
        '161715.XSHE', #大宗商品
        '513500.XSHG', #标普500
        
    ]
    g.m_days = 25 #动量参考天数
    g.target_num = 2 #
    g.count=0
    g.target_list=[]
    run_daily(trade, '9:30') #每天运行确保即时捕捉动量变化

def get_rank(etf_pool):
    score_list = [] 
    #计算动量
    for etf in etf_pool:    
        df = attribute_history(etf, g.m_days, '1d', ['open'])
        y = df['log'] = np.log(df.open)
        x = df['num'] = np.arange(df.log.size)
        slope, intercept = np.polyfit(x, y, 1)
        annualized_returns = math.pow(math.exp(slope), 100) - 1
        r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
        #按照收益率预期与线性拟合稳定性进行排名
        score = annualized_returns * r_squared
        score_list.append(score)
    df = pd.DataFrame(index=etf_pool, data={'score':score_list})
    df = df.sort_values(by='score', ascending=False)
    # df_positive = df[df['score'] > 0]
    # g.target_num = max(1,min(len(df_positive),3))
    # rank_list = list(df_positive.index)    
    rank_list = list(df.index)
    # print(df)     
    record(黄金 = round(df.loc['518880.XSHG'], 2))
    record(纳指 = round(df.loc['513100.XSHG'], 2))
    record(创业 = round(df.loc['159915.XSHE'], 2))
    record(中大 = round(df.loc['510180.XSHG'], 2))
    record(金融 = round(df.loc['510650.XSHG'], 2))
    record(医药 = round(df.loc['510660.XSHG'], 2))
    record(大宗 = round(df.loc['161715.XSHE'], 2))
    record(标普 = round(df.loc['513500.XSHG'], 2))
    return rank_list

# 交易
def trade(context):
    # 获取动量最高的N只ETF
    
    target_list = get_rank(g.etf_pool)[:g.target_num]
    target_num=g.target_num
    # 卖出    
    hold_list = list(context.portfolio.positions)
    for etf in hold_list:
        if etf not in target_list:
            order_target_value(etf, 0)
            print('卖出' + str(etf))
        else:
            print('继续持有' + str(etf))
    # 买入
    hold_list = list(context.portfolio.positions)
    if len(hold_list) < target_num:
        value = context.portfolio.available_cash / (target_num - len(hold_list))
        for etf in target_list:
            if context.portfolio.positions[etf].total_amount == 0:
                order_target_value(etf, value)
                print('买入' + str(etf))
    g.count=g.count=1
