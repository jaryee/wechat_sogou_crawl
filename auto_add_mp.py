# -*- coding: utf-8 -*-
#添加指定公众号到爬虫数据库

# 导入包
from wechatsogou.tools import *
from wechatsogou import *
from PIL import Image
import datetime
import time
import sys,locale
import logging
import logging.config

# 日志
logging.config.fileConfig('auto_add_mp_logging.conf')
logger = logging.getLogger()

# 搜索API实例
wechats = WechatSogouApi()

#数据库实例
mysql = mysql('add_mp_list')
add_list = mysql.find(0)
succ_count = 0

for add_item in add_list :
    try:
        print(add_item)
        if add_item['wx_hao']:
            print("add by wx_hao")
            mysql.where_sql = "wx_hao ='" + add_item['wx_hao'] + "'"
            mp_data = mysql.table('mp_info').find(1)
            if not mp_data :
                wechat_info = wechats.get_gzh_info(add_item['wx_hao'])
                time.sleep(1)
                #print(wechat_info)
                if(wechat_info != ""):
                    mysql.table('mp_info').add({'name':wechat_info['name'],
                                                'wx_hao':wechat_info['wechatid'],
                                                'company':wechat_info['renzhen'],
                                                'description':wechat_info['jieshao'],
                                                'logo_url':wechat_info['img'],
                                                'qr_url': wechat_info['qrcode'],
                                                'wz_url': wechat_info['url'],
                                                'last_qunfa_id': 0,
                                                'create_time':time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))})
            else:
                print(u"已经存在的公众号")
        elif add_item['name']:
            #获取对应信息
            print("add by name")
            wechat_infos = wechats.search_gzh_info(add_item['name'].encode('utf8'))
            time.sleep(1)
            #print(wechat_infos)
            for wx_item in wechat_infos :
                #公众号数据写入数据库
                #搜索一下是否已经存在
                print(wx_item['name'])
                mysql.where_sql = "wx_hao ='" + wx_item['wechatid'] + "'"
                print(mysql.where_sql)
                mp_data = mysql.table('mp_info').find(1)
                if not mp_data :
                    print(wx_item['name'].decode("utf-8"))
                    mysql.table('mp_info').add({ 'name':wx_item['name'],
                                'wx_hao':wx_item['wechatid'],
                                'company':wx_item['renzhen'],
                                'description':wx_item['jieshao'],
                                'logo_url':wx_item['img'],
                                'qr_url': wx_item['qrcode'],
                                'wz_url': wx_item['url'],
                                'last_qunfa_id': 0,
                                'create_time':time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))})
                else:
                    print(u"已经存在的公众号")
                
        #删除已添加项
        mysql.table('add_mp_list').where({'_id':add_item['_id']}).delete()
    except:
        print(u"出错，继续")
        continue


print("success")

    

