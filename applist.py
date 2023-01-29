#!/usr/bin/python
# -*- coding: utf-8 -*-
# 引用 json 库用于解析 json 对象
import json
# 使用 requests 库
import requests
# 使用postgre数据库
import psycopg2

import re

response = requests.get('http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json')
gameInfo = response.text
# versionInfo 是接口返回的 json 格式数据
# json.loads 将已编码的 JSON 字符串解码为 Python 对象
gameInfoPython = json.loads(gameInfo) 
# print(list(list(versionInfoPython.values())[0].values())[0])
# 从字典里取 data 数组
dataList = gameInfoPython.get('applist').get('apps')
# print(dataList)
con = psycopg2.connect(host="localhost", database="", user="", password="")
cur = con.cursor()
punctuation ="""！？｡＂＃＄％＆＇（）＊＋－／：；＜＝＞＠［＼］＾＿｀｛｜｝
            ～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘'‛“”„‟…‧﹏®™!\"#$%&\'()+,-./:;<=>?@[\\]^_`{|}~"""

re_punctuation ="[{}]+".format(punctuation)

#line =re.sub(re_punctuation, "", line)
#match = re.sub(re_punctuation,"",title).lower()
for g in dataList:
   # print(g.get("appid"))
   # print(g.get("name"))
    title = g.get('name')
    detail_url = "https://store.steampowered.com/app/" + str(g.get('appid'))
    print(detail_url)
    match = re.sub(re_punctuation,"",title).lower()
    cur.execute('''insert into gameinfo (title, url, match) values (%s, %s, %s) ON CONFLICT (title) 
                DO update set match = %s where gameinfo.url = %s;'''
                ,[title, detail_url, match, match, detail_url])
