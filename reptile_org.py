# -*- coding=utf-8 -*-
import requests
from lxml import etree
import os
import re
import time
import database_op

'''
需求：爬取深市创业板披露类型为申报稿的公司的招股说明书 http://eid.csrc.gov.cn/ipo/101012/index_1_f.html
需求：爬取沪市科创板披露类型为申报稿的公司的招股说明书 http://eid.csrc.gov.cn/ipo/101013/index_1_f.html
第一次爬取一共368条数据
'''
# 将存储路径写成全局变量
sz_save_dir = './total_pdf_dir/sz/'  # 深市所有招股说明书PDF文件
sh_save_dir = './total_pdf_dir/sh/'  # 沪市所有招股说明书PDF文件

def downloadPDF(url, data, save_dir):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
    }
    for pageNum in range(1, 51):  # 一共50页
        insert_data = []    # 爬取一页数据往数据库里插入一次
        # 对应页码的url
        complete_url = format(url % pageNum)
        # 使用通用爬虫对url对应的一整张页面进行爬取
        page_text = requests.post(url=complete_url, headers=headers, data=data).text
        # 使用聚焦爬虫将页面中所有的PDF进行解析/提取
        tree = etree.HTML(page_text)
        tr_list = tree.xpath('//table[@class="m-table2 m-table2-0"]//tr[@onclick]')
        for tr in tr_list:
            notice_td_title = tr.xpath('./td[6]/@title')[0]
            if (notice_td_title == '招股说明书'):
                company_name = tr.xpath('./td[1]/text()')[0]  # 公司名称
                listed_block = re.sub(r'[\s\xa0&nbsp]', '', tr.xpath('./td[3]/text()')[0])  # 上市版块,消除换行符和空格
                sponsor = tr.xpath('./td[4]/li/text()')[0]  # 保荐人/保荐机构
                publish_date = tr.xpath('./td[5]/text()')[0]  # 披露时间
                file_url = re.search('http.*?pdf', tr.xpath('./@onclick')[0], re.S).group()  # 文件url
                # 请求到了文件的二进制数据
                file_data = requests.get(url=file_url, headers=headers).content
                # 获取文件名称
                file_name = file_url.split('/')[-1]
                # 文件存储的路径
                file_path = save_dir + file_name
                with open(file_path, 'wb') as fp:
                    fp.write(file_data)
                    print(file_name, '下载成功！！！')
                create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                insert_data.append([file_name,company_name,create_time,listed_block,sponsor,publish_date])
        # 将数据插入数据库
        database_op.insert_many_data_by_reptile(insert_data)

if __name__ == "__main__":
    # 创建两个文件夹，分别保存深市和沪市所有的PDF文件
    if not os.path.exists(sz_save_dir):
        os.makedirs(sz_save_dir)
    if not os.path.exists(sh_save_dir):
        os.makedirs(sh_save_dir)
    # 设置一个通用的url模板
    sz_url = 'http://eid.csrc.gov.cn/ipo/101012/index_%d_f.html'  # 50页 4524条数据(不等于申报稿文件个数)
    sh_url = 'http://eid.csrc.gov.cn/ipo/101013/index_%d_f.html'  # 50页 2344条数据(不等于申报稿文件个数)
    sz_data = {
        'prodType3': '',
        'prodType4': '',
        'keyWord': '',
        'keyWord2': '关键字',
        'selBoardCode': '03',  # 03代表申报稿
        'selCatagory2': '10013',
        'startDate': '',
        'startDate2': '请输入开始时间',
        'endDate': '',
        'endDate2': '请输入结束时间',
    }
    sh_data = {
        'prodType3': '',
        'prodType4': '',
        'keyWord': '',
        'keyWord2': '关键字',
        'selBoardCode': '03',  # 03代表申报稿
        'selCatagory2': '10014',
        'startDate': '',
        'startDate2': '请输入开始时间',
        'endDate': '',
        'endDate2': '请输入结束时间',
    }
    downloadPDF(sz_url, sz_data, sz_save_dir)
    downloadPDF(sh_url, sh_data, sh_save_dir)
