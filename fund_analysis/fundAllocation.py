import pandas as pd
import numpy as np
import cvxpy as cp
import scipy.optimize as opt

def mean_variance_opt(df_mean,df_cov):
    assets = df_mean.index
    ret = df_mean.values
    cov = df_cov.values
    n = len(assets)
    w = cp.Variable(n)
    objective = cp.Minimize(cp.quad_form(w,cov))
    constraints = [w>=0]
    constraints += [ret @ w >= 0.1]
    problem = cp.Problem(objective,constraints)
    problem.solve()
    results = w.value/sum(w.value)
    return pd.Series(results,index=assets)

def risk_parity_alternative(df_cov):
    assets = df_cov.index
    cov = df_cov.values
    n = len(assets)
    w = cp.Variable(n)
    target = 0
    p_variance = w.T @ cov @ w
    for i in range(n):
        denominator = cov[i,:] @ w * n
        target += (w[i] - p_variance/denominator)**2
    constraints = [w>=0,sum(w)== 1 ]
    objective = cp.Minimize(target)
    problem = cp.Problem(objective,constraints)
    problem.solve()
    return pd.Series(w.value, index=assets)

def risk_parity(df_cov):

    assets = df_cov.index
    cov = df_cov.values
    n = len(assets)
    w0 = np.repeat(1/n,n)
    A = np.repeat(1,n)[np.newaxis,:]
    lb = np.array([1])
    ub = np.array([1])
    constraints = opt.LinearConstraint(A=A,lb=lb,ub=ub)
    bounds = opt.Bounds(ub=np.repeat(np.inf,n),lb=np.repeat(0,n))
    def target(w):
        target = 0
        p_variance = w.T.dot(cov).dot(w)
        for i in range(n):
            denominator = cov[i, :].dot(w) * n
            target += (w[i] - p_variance / denominator) ** 2
        return target

    res = opt.minimize(target,w0,method='SLSQP',constraints=constraints,bounds=bounds)

    return pd.Series(res.x, index=assets)


df_meta = pd.read_excel(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Asset Allocation Low Risk.xlsx',
                        sheet_name='Candidate', index_col='Index')
df_meta['Fund ID'] = df_meta['Fund ID'].map(lambda x: '0' * (6 - len(str(x))) + str(x))
fund_list = df_meta['Fund ID']
fund_name = df_meta['Fund Name']
fund_mapping = dict(zip(fund_list, fund_name))

df = pd.read_csv(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Fund Return\Low Risk Return.csv',index_col=0,parse_dates=['Date'])
df.columns = df.columns.map(lambda x: '0'*(6-len(str(x)))+str(x))
candidates = ['003327','000171','000215','519062']
df = df[candidates]
df_month = df.resample('M').last()
df_month = df_month.pct_change()
date = '2020/01/31'

df_ewcorr = df_month.ewm(halflife=60,min_periods=36).corr().loc[date]
df_ewcov = df_month.ewm(halflife=60,min_periods=36).cov().loc[date]
df_ewcorr.index = df_ewcorr.index.get_level_values(1)
df_ewcov.index = df_ewcov.index.get_level_values(1)
df_mean = df_month.mean()
df_cov = df_ewcov.dropna(axis=1).dropna(axis=0)
df_mean = df_mean.reindex(df_cov.index)

results = pd.DataFrame(index=candidates)
results.loc[:,'fund_name'] = results.index.map(lambda x: fund_mapping[x])
results.loc[:,'return'] = 12*df_mean
results.loc[:,'vol'] = np.sqrt(12)*df_month.std()
results.loc[:,'ret over risk'] = results.loc[:,'return']/results.loc[:,'vol']
results.loc[:,'mean_variance_optimization'] = mean_variance_opt(df_mean,df_cov)
results.loc[:,'risk_parity'] = risk_parity(df_cov)

results.to_excel(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\LowRiskAllocationResults.xlsx')