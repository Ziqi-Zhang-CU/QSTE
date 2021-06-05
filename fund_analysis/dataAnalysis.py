import pandas as pd
import numpy as np
import cvxpy as cvx
import datetime as dt


def calculate_drawdown(ts,years=50):
    start_date = ts.index[-1]-pd.DateOffset(years=years)
    ts = ts[start_date:]
    previous_high_price = ts.iloc[0]
    previous_high_price_date = ts.index[0]
    max_drawdown = 0
    max_drawdown_start = ts.index[0]
    max_drawdown_end = ts.index[0]
    max_drawdown_period_start = ts.index[0]
    max_drawdown_period_end = ts.index[0]
    max_drawdown_period = 0

    for date in ts.index:
        price = ts[date]
        if previous_high_price <= price :
            drawdown_period = (date - previous_high_price_date).days - 1
            if drawdown_period >= max_drawdown_period:
                max_drawdown_period_start = previous_high_price_date
                max_drawdown_period_end = date
                max_drawdown_period = (max_drawdown_period_end - max_drawdown_period_start).days
            previous_high_price = price
            previous_high_price_date = date
        else:
            drawdown = price/previous_high_price - 1
            if drawdown <= max_drawdown:
                max_drawdown_start = previous_high_price_date
                max_drawdown_end = date

        drawdown_period = (date - previous_high_price_date).days - 1
        if drawdown_period >= max_drawdown_period:
            max_drawdown_period_start = previous_high_price_date
            max_drawdown_period_end = date
            max_drawdown_period = (max_drawdown_period_end - max_drawdown_period_start).days
        previous_high_price = price
        previous_high_price_date = date
    index = ['max DD','max DD start', 'max DD end', 'max DD period', 'max DD period start', 'max DD period end']
    result = pd.Series([max_drawdown, max_drawdown_start, max_drawdown_end, max_drawdown_period, max_drawdown_period_start, max_drawdown_period_end],index=index)

    return result

def calculate_beta(ts,years=50):
    start_date = ts.index[-1]-pd.DateOffset(years=years)
    ts = ts[start_date:]
    ts_csi_300 = pd.read_csv(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Fund Return\csi300.csv',parse_dates=['Date'],index_col=0)['Index']
    ts_csi_300 = ts_csi_300.resample('D').last().fillna(method='bfill').reindex(ts.index)
    ts_csi_300 = ts_csi_300 .pct_change()
    ts_rf = pd.read_csv(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Fund Return\Riskfree.csv',parse_dates=['Date'],index_col=0)['Index']/100
    ts_rf = ts_rf.map(float)
    ts_rf = ts_rf.resample('D').last().fillna(method='bfill').reindex(ts.index)/12
    ts_excess = ts - ts_rf
    ts_csi_300_excess = ts_csi_300 - ts_rf
    beta = (ts_excess.ewm(halflife=60,min_periods=36).cov(other = ts_csi_300_excess)/ts_csi_300_excess.ewm(halflife=60,min_periods=36).var()).iloc[-1]
    return beta

def calculate_mean_vol(ts,years=50):
    results = pd.Series()
    ts_3m = ts[ts.index[-1]-pd.DateOffset(months=3):]
    ts_6m = ts[ts.index[-1]-pd.DateOffset(months=6):]
    ts_1y = ts[ts.index[-1]-pd.DateOffset(years=1):]
    ts_3y = ts[ts.index[-1]-pd.DateOffset(years=3):]
    ts_5y = ts[ts.index[-1]-pd.DateOffset(years=5):]
    ts_full = ts[:]

    ts_rf = pd.read_csv(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Fund Return\Riskfree.csv',parse_dates=['Date'],index_col=0)['Index']/100
    ts_rf = ts_rf.map(float)
    ts_rf = ts_rf.resample('D').last().fillna(method='bfill').reindex(ts.index)/12

    ts_excess_3m = ts_3m - ts_rf[ts_rf.index[-1]-pd.DateOffset(months=3):]
    ts_excess_6m = ts_6m - ts_rf[ts_rf.index[-1]-pd.DateOffset(months=6):]
    ts_excess_1y = ts_1y - ts_rf[ts_rf.index[-1]-pd.DateOffset(years=1):]
    ts_excess_3y = ts_3y - ts_rf[ts_rf.index[-1]-pd.DateOffset(years=3):]
    ts_excess_5y = ts_5y - ts_rf[ts_rf.index[-1]-pd.DateOffset(years=5):]
    ts_excess_full = ts_full - ts_rf[:]

    results.loc['3M return'] = ts_3m.mean()*12
    results.loc['6M return'] = ts_6m.mean()*12
    results.loc['1Y return'] = ts_1y.mean()*12
    results.loc['3Y return'] = ts_3y.mean()*12
    results.loc['5Y return'] = ts_5y.mean()*12
    results.loc['Full return'] = ts_full.mean()*12

    results.loc['3M vol'] = ts_3m.std()*np.sqrt(12)
    results.loc['6M vol'] = ts_6m.std()*np.sqrt(12)
    results.loc['1Y vol'] = ts_1y.std()*np.sqrt(12)
    results.loc['3Y vol'] = ts_3y.std()*np.sqrt(12)
    results.loc['5Y vol'] = ts_5y.std()*np.sqrt(12)
    results.loc['Full vol'] = ts_full.std()*np.sqrt(12)

    results.loc['3M Sharpe'] = ts_excess_3m.mean()/ts_excess_3m.std()*np.sqrt(12)
    results.loc['6M Sharpe'] = ts_excess_6m.mean()/ts_excess_6m.std()*np.sqrt(12)
    results.loc['1Y Sharpe'] = ts_excess_1y.mean()/ts_excess_1y.std()*np.sqrt(12)
    results.loc['3Y Sharpe'] = ts_excess_3y.mean()/ts_excess_3y.std()*np.sqrt(12)
    results.loc['5Y Sharpe'] = ts_excess_5y.mean()/ts_excess_5y.std()*np.sqrt(12)
    results.loc['Full Sharpe'] = ts_excess_full.mean()/ts_excess_full.std()*np.sqrt(12)

    return results

def generate_summary(ts,years=50):
    results = calculate_mean_vol(ts,years)
    results.loc['beta'] = calculate_beta(ts,years)
    #results = pd.concat([results,calculate_drawdown(ts,years)])
    results.name = ts.name
    return results



df_meta = pd.read_excel(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Asset Allocation.xlsx',
                        sheet_name='Candidate', index_col='Index')
df_meta['Fund ID'] = df_meta['Fund ID'].map(lambda x: '0' * (6 - len(str(x))) + str(x))
fund_list = df_meta['Fund ID']
fund_name = df_meta['Fund Name']
fund_mapping = dict(zip(fund_list, fund_name))

df = pd.read_csv(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Fund Return\Complete.csv',index_col=0,parse_dates=['Date'])
df.columns = df.columns.map(lambda x: '0'*(6-len(str(x)))+str(x))
df_month = df.resample('M').last()
df_month = df_month.pct_change()
date = '2020/12/31'

summary = df_month.apply(generate_summary)

df_ewcorr = df_month.ewm(halflife=60,min_periods=36).corr().loc[date]
df_ewcov = df_month.ewm(halflife=60,min_periods=36).cov().loc[date]
df_ewcorr.index = df_ewcorr.index.get_level_values(1)
df_ewcov.index = df_ewcov.index.get_level_values(1)
df_mean = df_month.mean()
df_cov = df_ewcov.dropna(axis=1).dropna(axis=0)
df_mean = df_mean.reindex(df_cov.index)

with pd.ExcelWriter(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Fund Return\risk_0118.xlsx') as writer:
    df_ewcorr.to_excel(writer,sheet_name='Correlation')
    df_ewcov.to_excel(writer,sheet_name='Covariance')
    summary.to_excel(writer,sheet_name='Summary')


