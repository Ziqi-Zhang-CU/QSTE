# 导入需要的模块
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import pandas as pd

def get_url(url, params=None, proxies=None):
    rsp = requests.get(url, params=params, proxies=proxies)
    rsp.raise_for_status()
    return rsp.text

def get_fund_data(code,per=10,sdate='',edate='',proxies=None):
    url = 'http://fund.eastmoney.com/f10/F10DataApi.aspx'
    params = {'type': 'lsjz', 'code': code, 'page':1,'per': per, 'sdate': sdate, 'edate': edate}
    html = get_url(url, params, proxies)
    soup = BeautifulSoup(html, 'html.parser')

    pattern=re.compile(r'pages:(.*),')
    result=re.search(pattern,html).group(1)
    pages=int(result)

    # 获取表头
    heads = []
    for head in soup.findAll("th"):
        heads.append(head.contents[0])

    # 数据存取列表
    records = []

    # 从第1页开始抓取所有页面数据
    page=1
    while page<=pages:
        params = {'type': 'lsjz', 'code': code, 'page':page,'per': per, 'sdate': sdate, 'edate': edate}
        html = get_url(url, params, proxies)
        soup = BeautifulSoup(html, 'html.parser')
        print('fetching fund %s page %s data' %(code,page))


        # 获取数据
        for row in soup.findAll("tbody")[0].findAll("tr"):
            row_records = []
            for record in row.findAll('td'):
                val = record.contents

                # 处理空值
                if val == []:
                    row_records.append(np.nan)
                else:
                    row_records.append(val[0])

            # 记录数据
            records.append(row_records)

        # 下一页
        page=page+1

    # 数据整理到dataframe
    np_records = np.array(records)
    data= pd.DataFrame()
    for col,col_name in enumerate(heads):
        data[col_name] = np_records[:,col]

    return data


# 主程序
if __name__ == "__main__":
    df_meta = pd.read_excel(r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Asset Allocation Low Risk.xlsx',sheet_name='Candidate',index_col='Index')
    df_meta['Fund ID'] = df_meta['Fund ID'].map(lambda x: '0'*(6-len(str(x)))+str(x))
    fund_list = df_meta['Fund ID']
    fund_name = df_meta['Fund Name']
    fund_mapping = dict(zip(fund_list,fund_name))
    start_date = '2010-01-01'
    end_date = '2021-02-01'
    file_path = r'C:\Users\mrzha\OneDrive\Documents\AssetAllocation\Fund Return'
    df_all = pd.DataFrame(index=pd.date_range(start_date,end_date,freq='D'),columns=fund_list)
    for fund in fund_list:
        data=get_fund_data(fund,per=50,sdate=start_date,edate=end_date)
        # 修改数据类型
        data['Date']=pd.to_datetime(data['净值日期'],format='%Y/%m/%d')
        data['Index']= data['单位净值'].astype(float)
        data['Total Return Index']=data['累计净值'].astype(float)
        data['Return']=data['日增长率'].str.strip('%').astype(float)
        # 按照日期升序排序并重建索引
        data=data.sort_values(by='Date',axis=0,ascending=True).reset_index(drop=True)
        data = data.set_index('Date')
        data.to_csv(file_path+'\\'+fund+'.csv')
        ts = data['Total Return Index']
        ts.name = fund
        df_all[fund].update(ts)
    df_all.to_csv(file_path+'\\Low Risk Return.csv')

