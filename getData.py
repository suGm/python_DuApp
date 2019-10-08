#coding:UTF-8

import re
import json
import pymysql
import requests
import time, datetime
import random
from bs4 import BeautifulSoup

def conMysql():
	con = pymysql.connect(
		host = '127.0.0.1',user = 'root',passwd = 'abcdefg',
		port = 3306,db = 'duApp',charset = 'utf8' #port必须写int类型 #charset必须写utf8，不能写utf-8
	)
	return con
	# cur = coon.cursor()  #建立游标
 	# cur.execute("select * from stu")  #查询数据
	# res = cur.fetchall()    #获取结果
	# cur.execute('insert into stu(name,sex) VALUE ("pzp","man");')

def closeMysql(con, cur):
	cur.close() #关闭游标
	con.close() #关闭连接

def selectMysql(cur, sql):
	cur.execute(sql) #查询数据
	res = cur.fetchall() #获取结果
	return res

def insertMysql(con, cur, sql):
	cur.execute(sql)

def getContent(index):
	content = requests.get('https://www.poizon.com/product-detail?productId=' + index)
	content.encoding = 'UTF-8'
	html = BeautifulSoup(content.text,'html.parser')
	data = html.find("script", {'id': '__NEXT_DATA__'})
	return data

def replaceStr(_str):
	_str = str(_str)
	_str = _str.replace('\\', '\\\\')
	_str = _str.replace('\'', '\\\'')
	_str = _str.replace('"', '\"')
	return _str

con = conMysql()
cur = con.cursor(cursor=pymysql.cursors.DictCursor) # 作为字典返回
writeFile = open('C:\\Users\\Administrator\\Desktop\\python\\fail1.txt', 'a')
print('初始化:正在爬取数据...')
maxProductIdSql = 'select product_id from shoes_info order by product_id desc limit 1;'
maxProductId = selectMysql(cur, maxProductIdSql)
rangeMin = maxProductId[0]['product_id']
rangeMax = rangeMin + 200

for i in range(rangeMin, rangeMax):
	i = str(i)

	selSql = 'select id from shoes_info where product_id = ' + i #判断当前数据库是否存在数据
	shoeData = selectMysql(cur, selSql)
	if shoeData :#存在该条数据则跳过
		continue

	print('爬取数据货物id为'+ i +'的数据...')

	dataStr = getContent(i)#爬取数据

	print('处理数据货物id为'+ i +'的数据...')
	dataContent = dataStr.get_text() #获取当前有用数据内容
	contentObj = json.loads(dataContent)

	if 'detail' in contentObj['props']['initialState']['productDetail']['detail'] : #如果没有了则跳出循环
		newContentObj = contentObj['props']['initialState']['productDetail']['detail']['detail']

		if newContentObj['typeId'] != 0: #typeId为0的代表是鞋子
			print('货物id为'+ i +'的数据不是鞋子,跳过...')
			# time.sleep(random.random())
			continue
		
		insertDataObj = dict()
		insertDataObj['shoes_name'] = 'title' in newContentObj and replaceStr(newContentObj['title']) or ''
		insertDataObj['shoes_number'] = 'articleNumber' in newContentObj and newContentObj['articleNumber'] or ''
		insertDataObj['shoes_color'] = 'color' in newContentObj and replaceStr(newContentObj['color']) or ''
		insertDataObj['shoes_sizeList'] = 'sizeList' in newContentObj and json.dumps(newContentObj['sizeList']) or ''
		insertDataObj['sell_day'] = 'sellDate' in newContentObj and newContentObj['sellDate'] or ''
		insertDataObj['product_id'] = i
		insertDataObj['logo'] = 'logoUrl' in newContentObj and newContentObj['logoUrl'] or ''

		insertDataKeysArr = []
		insertDataValuesArr = []
		for x in insertDataObj:
			insertDataKeysArr.append(x)
			insertDataValuesArr.append(insertDataObj[x])
		insertInfoSql = 'insert into shoes_info(`'+ '`,`'.join(insertDataKeysArr) +'`) values(\''+ '\',\''.join(insertDataValuesArr) +'\');'#构造插入shoes_info数据

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
		inserPriceSql = 'insert into shoes_prices(`product_id`,`'+ '`,`'.join(inserKeysArr) +'`, `write_time`) values(' + i + ',' + ','.join(inserValuesArr) +',now());'#构造插入shoes_prices数据

		print('数据货物id为'+ i +'的数据处理完毕')
		print('正在插入货物id为'+ i +'的数据')
		try:
			insertMysql(con, cur, insertInfoSql)
			insertMysql(con, cur, inserPriceSql)
		except Exception as e:
		    con.rollback()  # 事务回滚
		    print('事务处理失败', e)
		    writeFile.write('写入失败货物编号:'+i+'\n')
		    writeFile.write(insertInfoSql+'\n')
		    writeFile.write(inserPriceSql+'\n')
		else:
		    con.commit()  # 事务提交
		    print('事务处理成功', cur.rowcount)
		print('货物id为'+ i +'的数据处理完成')
	# elif int(i) < 49850:
		# time.sleep(random.random())
		# continue
	# else :
		# break
	# time.sleep(random.random())

writeFile.close()
closeMysql(con, cur)
print('数据爬取结束')