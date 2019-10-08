#coding:UTF-8
#任务计划程序 每天晚上8点定时执行
import re
import json
import pymysql
import requests
import time, datetime
import random
from bs4 import BeautifulSoup

# 连接mysql
def conMysql():
	con = pymysql.connect(
		host = '127.0.0.1', user = 'root', passwd = 'abcdefg',
		port = 3306, db = 'duApp', charset = 'utf8'
	)
	return con

# 关闭mysql
def closeMysql(con, cur):
	cur.close()
	con.close()

# 查询sql语句
def selMysql(cur, sql):
	cur.execute(sql)
	res = cur.fetchall()
	return res

# 爬取链接
def getContent(index):
	content = requests.get('https://www.poizon.com/product-detail?productId=' + index)

	content.coding = 'UTF-8'
	html = BeautifulSoup(content.text, 'html.parser')
	data = html.find('script', {'id': '__NEXT_DATA__'})
	return data

def replaceStr(_str):
	_str = str(_str)
	_str = _str.replace('\\', '\\\\')
	_str = _str.replace('\'', '\\\'')
	_str = _str.replace('"', '\"')
	return _str

con = conMysql()
cur = con.cursor(cursor=pymysql.cursors.DictCursor)#字典形式返回

selSql = 'select product_id from shoes_photo_data'
indexDict = selMysql(cur, selSql)

for i in indexDict:
	index = str(i['product_id'])

	newSelSql = 'select id from shoes_info where product_id =' + index
	result = selMysql(cur, newSelSql)
	
	dataStr = getContent(index)
	dataContent = dataStr.get_text() #获取当前有用数据内容
	contentObj = json.loads(dataContent)

	newContentObj = contentObj['props']['initialState']['productDetail']['detail']['detail']

	if newContentObj['typeId'] != 0: #typeId为0的代表是鞋子
		time.sleep(random.random())
		continue

	if 'detail' in contentObj['props']['initialState']['productDetail']['detail'] : #判断是否存在该产品
		if len(result) == 0: #该条信息在数据库中不存在
			#则需要在shoes_info中添加该信息
			insertDataObj = dict()
			insertDataObj['shoes_name'] = 'title' in newContentObj and replaceStr(newContentObj['title']) or ''
			insertDataObj['shoes_number'] = 'articleNumber' in newContentObj and newContentObj['articleNumber'] or ''
			insertDataObj['shoes_color'] = 'color' in newContentObj and replaceStr(newContentObj['color']) or ''
			insertDataObj['shoes_sizeList'] = 'sizeList' in newContentObj and json.dumps(newContentObj['sizeList']) or ''
			insertDataObj['sell_day'] = 'sellDate' in newContentObj and newContentObj['sellDate'] or ''
			insertDataObj['product_id'] = index
			insertDataObj['logo'] = 'logoUrl' in newContentObj and newContentObj['logoUrl'] or ''
			
			insertDataKeysArr = []
			insertDataValuesArr = []
			for x in insertDataObj:
				insertDataKeysArr.append(x)
				insertDataValuesArr.append(insertDataObj[x])
			insertInfoSql = 'insert into shoes_info(`'+ '`,`'.join(insertDataKeysArr) +'`) values(\''+ '\',\''.join(insertDataValuesArr) +'\');'#构造插入shoes_info数据
			try:
				cur.execute(insertInfoSql)
			except Exception as e:
				con.rollback()
			else:
				con.commit()
		# 插入价格
		sizeList = contentObj['props']['initialState']['productDetail']['detail']['sizeList']#鞋子价格数据
		inserKeysArr = []
		inserValuesArr = []
		for j in sizeList:
			try:
				fNumber = float(j['size']) #幼童等鞋子的鞋码代号为11C等所以过滤幼童
			except Exception as e:
				continue

			if int(j['item']['price']) == 0 or fNumber > 48 or fNumber < 36:
			    continue 	
			inserKeysArr.append('price_' + j['size'])
			inserValuesArr.append(str(int(j['item']['price'] / 100)))

		inserKeysArr.append('is_show')
		inserValuesArr.append(str(newContentObj['isShow']))
		inserPriceSql = 'insert into shoes_prices(`product_id`,`'+ '`,`'.join(inserKeysArr) +'`, `write_time`) values(' + index + ',' + ','.join(inserValuesArr) +',now());'#构造插入shoes_prices数据
		try:
			cur.execute(inserPriceSql)
		except Exception as e:
			con.rollback()
		else:
			con.commit()

	time.sleep(random.random())

closeMysql(con, cur)