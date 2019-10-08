#coding:UTF-8

import pymysql
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdate
import matplotlib.ticker as mtick


def conMysql():
	con = pymysql.connect(
		host = '127.0.0.1', user = 'root', passwd = 'abcdefg',
		port = 3306, db = 'duApp',charset = 'utf8'
	)
	return con

def closeMysql(con, cur):
	cur.close()
	con.close()

def selectMysql(cur, sql):
	cur.execute(sql)
	res = cur.fetchall()
	return res

con = conMysql()
cur = con.cursor(cursor=pymysql.cursors.DictCursor)

productId = '40748'

dataSql = 'select s.shoes_name, s.logo, sp.`price_36.5` as price, DATE_FORMAT(sp.write_time, "%Y-%m-%d") as time from shoes_info as s ' \
		  'left join shoes_prices as sp on s.product_id = sp.product_id ' \
		  'where s.product_id = '+ productId +' order by time limit 365'

dataRes = selectMysql(cur, dataSql)

closeMysql(con, cur)

print(dataRes[0]['time'], dataRes[-1]['time'])

# ax.set(xlabel='时间 (Y-m)', ylabel='价格 (rmb)',
#        title='关于鞋子xx的价格')

# plt.show()

prices = []
dates = []
shoesName = ''
for i in dataRes:
	dates.append(i['time'])
	prices.append(i['price'])
	shoesName = i['shoes_name']

shoesPhotoName = './prices_' + productId + '.png'
fig1 = plt.figure(figsize=(15, 10), dpi=80)
x1 = dates
print(dates)
y1 = prices
deg = len(dates) >= 30 and 90 or 0
plt.plot_date(x1,y1,'-')
plt.xticks(rotation=deg)
plt.xlabel('日期(Y-m-d)')
plt.ylabel('价格(rmb)')
plt.title(shoesName + "的价格走势")
plt.savefig(shoesPhotoName)
plt.show()
