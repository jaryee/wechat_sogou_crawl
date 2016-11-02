# -*- coding: utf-8 -*-
#更新文章阅读数据，目前一篇文章只监控24小时

# 导入包
from wechatsogou.tools import *
from wechatsogou import *
import _imaging
import datetime
import time
import logging
import logging.config

# 日志
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()


# 搜索API实例
wechats = WechatSogouApi()

#数据库实例
mysql.order_sql = " order by _id desc"
mysql = mysql('mp_info')

#循环获取数据库中所有公众号
mp_list = mysql.find(0)


now_time = datetime.datetime.now()
yes_time = now_time + datetime.timedelta(days=-1) #只更新1天之内的数据，可以修改days=-2就是2天
succ_count = 1

for item in mp_list:
    try:
        #为了效率，首先查看该公众号是否有24小时之内的文章
        mysql.where_sql = "mp_id=%d and date_time >'%s'" %(item['_id'],yes_time)
        wz_time = mysql.table('wenzhang_info').find(1)
        if not wz_time :
            continue

        print(item['name'])
        #print('1')
        wz_url = ""
        if item.has_key('wz_url') :
            wz_url = item['wz_url']
        else :
            wechat_info = wechats.get_gzh_info(item['wx_hao'])
            if not wechat_info.has_key('url') :
                continue
            wz_url = wechat_info['url'];

        #print('2')
        wz_list = wechats.get_gzh_message(url=wz_url)
        if u'链接已过期' in wz_list:
            wechat_info = wechats.get_gzh_info(item['wx_hao'])
            print(wechat_info)
            if not wechat_info.has_key('url') :
                continue
            print('guo qi sz chong xin huo qu success')
            wz_url = wechat_info['url'];
            wz_list = wechats.get_gzh_message(url=wz_url)
            mysql.table('mp_info').where({'_id':item['_id']}).save({'wz_url':wechat_info['url'],'logo_url':wechat_info['img'],'qr_url':wechat_info['qrcode']})
        #type==49表示是图文消息
        #print('3')
        for wz_item in wz_list :
            #只监控24小时之内的文章
            if(wz_item['datetime'] < time.mktime(yes_time.timetuple())):
                break

            if wz_item['type'] == '49':
                #获取文章数据
                time.sleep(1)
                article_info = wechats.deal_article(url=wz_item['content_url'])
                #print('4')
                # if(article_info['yuan'] == '') :
                #     continue
                #获取数据库记录
                #mysql.where_sql = "msg_index=%d" %(wz_item['main'])
                mysql.where_sql = "qunfa_id=%d and msg_index=%d" %(wz_item['qunfa_id'],wz_item['main'])
                #print(mysql.where_sql)
                wz_data = mysql.table('wenzhang_info').find(1)
                if not wz_data :
                    continue

                #获取当前的数据
                print(succ_count)
                succ_count += 1
                read_count = wz_data['read_count']
                like_count = wz_data['like_count']
                comment_count = wz_data['comment_count']
                print "%d new_read:%d  new_like:%d read:%d  like:%d" %(wz_data['_id'], article_info['comment']['read_num'],article_info['comment']['like_num'],read_count,like_count)
                #把文章写入数据库
                mysql.table('wenzhang_statistics').add({'wz_id':wz_data['_id'],
                                                'create_time':time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time())),
                                                'read_count':int(article_info['comment']['read_num'])-read_count,
                                                'like_count':int(article_info['comment']['like_num'])-like_count,
                                                'comment_count': int(article_info['comment']['elected_comment_total_cnt'])-comment_count})
                #print('5')
            #更新文章总阅读数
            mysql.table('wenzhang_info').where({'_id':wz_data['_id']}).save({'read_count':int(article_info['comment']['read_num']),
                                                                            'like_count':int(article_info['comment']['like_num']),
                                                                            'comment_count': int(article_info['comment']['elected_comment_total_cnt'])})
    except KeyboardInterrupt:
        break
    # except: #如果不想因为错误使程序退出，可以开启这两句代码
    #     continue
                
print('success')

