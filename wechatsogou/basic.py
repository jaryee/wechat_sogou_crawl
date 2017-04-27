# -*- coding: utf-8 -*-

import logging
import requests
import random
import time
import re
from lxml import etree
from PIL import Image
import cookielib
import json

try:
    from urllib.request import quote as quote
except ImportError:
    from urllib import quote as quote
    import sys

    reload(sys)
    sys.setdefaultencoding('utf-8')

try:
    import StringIO


    def readimg(content):
        return Image.open(StringIO.StringIO(content))
except ImportError:
    import tempfile


    def readimg(content):
        f = tempfile.TemporaryFile()
        f.write(content)
        return Image.open(f)

try:
    import urlparse as url_parse
except ImportError:
    import urllib.parse as url_parse

from lxml import etree
from PIL import Image

from . import config
from .base import WechatSogouBase
from .exceptions import *
from .ruokuaicode import RClient
from .filecache import WechatCache

import logging

logger = logging.getLogger()


class WechatSogouBasic(WechatSogouBase):
    """基于搜狗搜索的的微信公众号爬虫接口 基本功能类
    """

    def __init__(self, **kwargs):
        self._cache = WechatCache(config.cache_dir, 60 * 60)
        self._session = self._cache.get(config.cache_session_name) if self._cache.get(
            config.cache_session_name) else requests.session()
        
        self.cookies = ""
        cookies_file = kwargs.get('cookies_file')
        if cookies_file:
            #使用外部cookies
            print(u"使用外部cookies文件加载")
            cookie_jar = cookielib.MozillaCookieJar()  
            cookies = open(cookies_file.get('file_name')).read()
            for cookie in json.loads(cookies):  
                print cookie['name']
                cookie_jar.set_cookie(cookielib.Cookie(version=0, name=cookie['name'], value=cookie['value'], port=None, port_specified=False, domain=cookie['domain'], domain_specified=False, domain_initial_dot=False, path=cookie['path'], path_specified=True, secure=cookie['secure'], expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False))  
            self._session.cookies.update(cookie_jar)
        
        self.dama_name = config.dama_name
        self.dama_pswd = config.dama_pswd
        if self.dama_name != '' and self.dama_pswd != '':
           self._ocr = RClient(self.dama_name, self.dama_pswd, '70021', 'dcefe229cb9b4e1785b48fbc3525d011')

        self._agent = [
            "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0",
            "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        ]

    def _get_elem_text(self, elem):
        """抽取lxml.etree库中elem对象中文字

        Args:
            elem: lxml.etree库中elem对象

        Returns:
            elem中文字
        """
        rc = []
        for node in elem.itertext():
            rc.append(node.strip())
        return ''.join(rc)

    def _get_encoding_from_reponse(self, r):
        """获取requests库get或post返回的对象编码

        Args:
            r: requests库get或post返回的对象

        Returns:
            对象编码
        """
        encoding = requests.utils.get_encodings_from_content(r.text)
        return encoding[0] if encoding else requests.utils.get_encoding_from_headers(r.headers)

    def _get(self, url, rtype='get', **kwargs):
        """封装request库get,post方法

        Args:
            url: 请求url
            host: 请求host
            referer: 请求referer
            proxy: 是否启用代理请求

        Returns:
            text: 请求url的网页内容

        Raises:
            WechatSogouException: 操作频繁以致出现验证码或requests请求返回码错误
        """
        referer = kwargs.get('referer', None)
        host = kwargs.get('host', None)
        if host:
            del kwargs['host']
        if referer:
            del kwargs['referer']
        headers = {
            "Host": host if host else 'weixin.sogou.com',
            "Upgrade-Insecure-Requests":'1',
            "User-Agent": self._agent[random.randint(0, len(self._agent) - 1)],
            "Accept":'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            "Referer": referer if referer else 'http://weixin.sogou.com/',
            "Accept-Encoding":'gzip, deflate, sdch',
            "Accept-Language":'zh-CN,zh;q=0.8'
            
        }
        if rtype == 'get':
            #self._session.cookies.set
            r = self._session.get(url, headers=headers, **kwargs)
        else:
            data = kwargs.get('data', None)
            json = kwargs.get('json', None)
            r = self._session.post(url, data=data, json=json, headers=headers, **kwargs)
        
        #logger.error(r.text)
        if u'链接已过期' in r.text:
            return '链接已过期'
        if r.status_code == requests.codes.ok:
            r.encoding = self._get_encoding_from_reponse(r)
            if u'用户您好，您的访问过于频繁，为确认本次访问为正常用户行为，需要您协助验证' in r.text:
                self._vcode_url = url
                logger.error('出现验证码。。。')
                print(u'用户您好，您的访问过于频繁，为确认本次访问为正常用户行为，需要您协助验证')
                raise WechatSogouVcodeException('weixin.sogou.com verification code')
        else:
            logger.error('requests status_code error' + r.status_code)
            raise WechatSogouRequestsException('requests status_code error', r.status_code)
        return r.text

    def _jiefeng(self):
        """对于出现验证码，识别验证码，解封

        Args:
            ruokuai: 是否采用若快打码平台

        Raises:
            WechatSogouVcodeException: 解封失败，可能验证码识别失败
        """
        max_count = 0
        while(max_count < 10) :
            print(u"出现验证码，准备自动识别")
            max_count += 1
            logger.debug('vcode appear, using _jiefeng')
            codeurl = 'http://weixin.sogou.com/antispider/util/seccode.php?tc=' + str(time.time())[0:10]
            coder = self._session.get(codeurl)
            codeID = "0"
            
            if hasattr(self, '_ocr'):
                result = self._ocr.create(coder.content, 3060)
                if not result.has_key('Result') :
                    print(u"若快识别失败，1秒后更换验证码再次尝试，尝试次数：%d" %(max_count))
                    time.sleep(1)
                    continue #验证码识别错误，再次执行
                else:
                    print(u"验证码识别成功 验证码：%s" %(result['Result']))

                    img_code = result['Result']
                    codeID = result['Id']

                    post_url = 'http://weixin.sogou.com/antispider/thank.php'
                    post_data = {
                        'c': img_code,
                        'r': quote(self._vcode_url),
                        'v': 5
                    }
                    user_agent = self._agent[random.randint(0, len(self._agent) - 1)]
                    headers = {
                        "User-Agent": user_agent,
                        'Host': 'weixin.sogou.com',
                        'Referer': 'http://weixin.sogou.com/antispider/?from=%2f' + quote(
                            self._vcode_url.replace('http://', ''))
                    }
                    #time.sleep(3)
                    rr = self._session.post(post_url, post_data, headers=headers)
                    remsg = eval(rr.content)
                    if remsg['code'] != 0:
                        print(u"搜狗返回验证码错误，1秒后更换验证码再次启动尝试，尝试次数：%d" %(max_count))
                        time.sleep(1)
                        continue

                    #搜狗又增加验证码机制
                    time.sleep(0.05)
                    cookie_jar = cookielib.MozillaCookieJar()  
                    cookie_jar.set_cookie(cookielib.Cookie(version=0, name='SNUID', value=remsg['id'], port=None, port_specified=False, domain='sogou.com', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=None, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False))  
                    self._session.cookies.update(cookie_jar)

                    pbsnuid = remsg['id'] #pb_cookie['SNUID'].value
                    pbsuv = ''#pb_cookie['SUV'].value
                    print pbsnuid
                    print pbsuv
                    pburl = 'http://pb.sogou.com/pv.gif?uigs_productid=webapp&type=antispider&subtype=0_seccodeInputSuccess&domain=weixin&suv=%s&snuid=%s&t=%s' %(pbsuv,pbsnuid,str(time.time())[0:10])
                    
                    headers = {
                        "User-Agent": user_agent,
                        'Host': 'pb.sogou.com',
                        'Referer': 'http://weixin.sogou.com/antispider/?from=%2f' + quote(
                            self._vcode_url.replace('http://', ''))
                    }
                    self._session.get(pburl, headers=headers)
                    
                    time.sleep(0.5)
                    
                    print(u"搜狗返回验证码识别成功，继续执行")
                    self._cache.set(config.cache_session_name, self._session)
                    logger.error('verify code ocr: ' + remsg['msg'])
                    break
                
            else:
                print(u"没有设置自动识别模块用户名、密码，无法执行")
                break


            

    def _ocr_for_get_gzh_article_by_url_text(self, url):
        print(u"出现验证码，准备自动识别2")
        logger.debug('vcode appear, using _ocr_for_get_gzh_article_by_url_text')
        
        if hasattr(self, '_ocr'):
            max_count = 0
            while(max_count < 10):
                max_count += 1
                timestr = str(time.time()).replace('.', '')
                timever = timestr[0:13] + '.' + timestr[13:17]
                codeurl = 'http://mp.weixin.qq.com/mp/verifycode?cert=' + timever
                coder = self._session.get(codeurl)
                logger.debug('vcode appear, using _ocr_for_get_gzh_article_by_url_text')
                result = self._ocr.create(coder.content, 2040)
                if not result.has_key('Result') :
                    print(u"若快识别失败，1秒后更换验证码再次尝试，尝试次数：%d" %(max_count))
                    time.sleep(1)
                    continue #验证码识别错误，再次执行
                else:
                    print(u"若快识别成功 验证码：%s" %(result['Result']))

                    img_code = result['Result']
                    codeID = result['Id']

                    post_url = 'http://mp.weixin.qq.com/mp/verifycode'
                    post_data = {
                        'cert': timever,
                        'input': img_code
                    }
                    headers = {
                        "User-Agent": self._agent[random.randint(0, len(self._agent) - 1)],
                        'Host': 'mp.weixin.qq.com',
                        'Referer': url
                    }
                    rr = self._session.post(post_url, post_data, headers=headers)
                    remsg = eval(rr.text)
                    if remsg['ret'] != 0:
                        print(u"搜狗返回验证码错误，1秒后更换验证码再次启动尝试，尝试次数：%d" %(max_count))
                        time.sleep(1)
                        continue
                    
                    print(u"搜狗返回验证码识别成功，继续执行")
                    self._cache.set(config.cache_session_name, self._session)
                    logger.debug('ocr ', remsg['errmsg'])
                    break

                break
        else:
            print(u"没有设置自动识别模块用户名、密码，无法执行")


    def _replace_html(self, s):
        """替换html‘&quot;’等转义内容为正常内容

        Args:
            s: 文字内容

        Returns:
            s: 处理反转义后的文字
        """
        s = s.replace('&#39;', '\'')
        s = s.replace('&quot;', '"')
        s = s.replace('&amp;', '&')
        s = s.replace('&gt;', '>')
        s = s.replace('&lt;', '<')
        s = s.replace('&yen;', '¥')
        s = s.replace('amp;', '')
        s = s.replace('&lt;', '<')
        s = s.replace('&gt;', '>')
        s = s.replace('&nbsp;', ' ')
        s = s.replace('\\', '')
        return s

    def _replace_dict(self, dicts):
        retu_dict = dict()
        for k, v in dicts.items():
            retu_dict[self._replace_all(k)] = self._replace_all(v)
        return retu_dict

    def _replace_list(self, lists):
        retu_list = list()
        for l in lists:
            retu_list.append(self._replace_all(l))
        return retu_list

    def _replace_all(self, data):
        if isinstance(data, dict):
            return self._replace_dict(data)
        elif isinstance(data, list):
            return self._replace_list(data)
        elif isinstance(data, str):
            return self._replace_html(data)
        else:
            return data

    def _str_to_dict(self, json_str):
        json_dict = eval(json_str)
        return self._replace_all(json_dict)

    def _replace_space(self, s):
        s = s.replace(' ', '')
        s = s.replace('\r\n', '')
        return s

    def _get_url_param(self, url):
        result = url_parse.urlparse(url)
        return url_parse.parse_qs(result.query, True)

    def _search_gzh_text(self, name, page=1):
        """通过搜狗搜索获取关键字返回的文本

        Args:
            name: 搜索关键字
            page: 搜索的页数

        Returns:
            text: 返回的文本
        """
        request_url = 'http://weixin.sogou.com/weixin?query=' + quote(
            name) + '&_sug_type_=&_sug_=n&type=1&page=' + str(page) + '&ie=utf8'
        try:
            text = self._get(request_url)
        except WechatSogouVcodeException:
            
            try:
                self._jiefeng()
                text = self._get(request_url, 'get', 
                                referer='http://weixin.sogou.com/antispider/?from=%2f' + quote(
                                    self._vcode_url.replace('http://', '')))
            except WechatSogouVcodeException:
                text = ""

        return text

    def _search_article_text(self, name, page=1):
        """通过搜狗搜索微信文章关键字返回的文本
        Args:
            name: 搜索文章关键字
            page: 搜索的页数

        Returns:
            text: 返回的文本
        """
        request_url = 'http://weixin.sogou.com/weixin?query=' + quote(
            name) + '&_sug_type_=&_sug_=n&type=2&page=' + str(page) + '&ie=utf8'

        try:
            text = self._get(request_url)
        except WechatSogouVcodeException:
            
            try:
                self._jiefeng()
                text = self._get(request_url, 'get', 
                                referer='http://weixin.sogou.com/antispider/?from=%2f' + quote(
                                  self._vcode_url.replace('http://', '')))
            except WechatSogouVcodeException:
                text = ""
        return text

    def _get_gzh_article_by_url_text(self, url):
        """最近文章页的文本

        Args:
            url: 最近文章页地址

        Returns:
            text: 返回的文本
        """

        text = self._get(url, 'get', host='mp.weixin.qq.com')
        
        if u'为了保护你的网络安全，请输入验证码' in text:
            print u'为了保护你的网络安全，请输入验证码'
            try:
                self._ocr_for_get_gzh_article_by_url_text(url)

                text = self._get(url, 'get', host='mp.weixin.qq.com')
            except:
                text = ""
        return text

    def _get_gzh_article_gzh_by_url_dict(self, text, url):
        """最近文章页  公众号信息

        Args:
            text: 最近文章文本

        Returns:
            字典{'name':name,'wechatid':wechatid,'jieshao':jieshao,'renzhen':renzhen,'qrcode':qrcodes,'img':img,'url':url}
            name: 公众号名称
            wechatid: 公众号id
            jieshao: 介绍
            renzhen: 认证，为空表示未认证
            qrcode: 二维码
            img: 头像图片
            url: 最近文章地址
        """
        page = etree.HTML(text)
        profile_info_area = page.xpath("//div[@class='profile_info_area']")[0]
        img = profile_info_area.xpath('div[1]/span/img/@src')[0]
        name = profile_info_area.xpath('div[1]/div/strong/text()')[0]
        name = self._replace_space(name)
        wechatid = profile_info_area.xpath('div[1]/div/p/text()')
        if wechatid:
            wechatid = wechatid[0].replace(u'微信号: ', '')
        else:
            wechatid = ''
        jieshao = profile_info_area.xpath('ul/li[1]/div/text()')[0]
        renzhen = profile_info_area.xpath('ul/li[2]/div/text()')
        renzhen = renzhen[0] if renzhen else ''
        qrcode = page.xpath('//*[@id="js_pc_qr_code_img"]/@src')[0]
        qrcode = 'http://mp.weixin.qq.com/' + qrcode if qrcode else ''
        return {
            'name': name,
            'wechatid': wechatid,
            'jieshao': jieshao,
            'renzhen': renzhen,
            'qrcode': qrcode,
            'img': img,
            'url': url
        }

    def _get_gzh_article_by_url_dict(self, text):
        """最近文章页 文章信息

        Args:
            text: 最近文章文本

        Returns:
            msgdict: 最近文章信息字典
        """
        try:
            msglist = re.findall("var msgList = (.+?)};", text, re.S)[0]
            msglist = msglist + '}'

            html = msglist
            html = html.replace('&#39;', '\'')
            html = html.replace('&amp;', '&')
            html = html.replace('&gt;', '>')
            html = html.replace('&lt;', '<')
            html = html.replace('&yen;', '¥')
            html = html.replace('amp;', '')
            html = html.replace('&lt;', '<')
            html = html.replace('&gt;', '>')
            html = html.replace('&nbsp;', ' ')
            html = html.replace('\\', '')

            msgdict = eval(html)
            return msgdict
        except:
            return ''

    def _deal_gzh_article_dict(self, msgdict, **kwargs):
        """解析 公众号 群发消息

        Args:
            msgdict: 信息字典

        Returns:
            列表，均是字典，一定含有一下字段qunfa_id,datetime,type

            当type不同时，含有不同的字段，具体见文档
        """
        biz = kwargs.get('biz', '')
        uin = kwargs.get('uin', '')
        key = kwargs.get('key', '')
        items = list()
        for listdic in msgdict['list']:
            item = dict()
            comm_msg_info = listdic['comm_msg_info']
            item['qunfa_id'] = comm_msg_info.get('id', '')  # 不可判重，一次群发的消息的id是一样的
            item['datetime'] = comm_msg_info.get('datetime', '')
            item['type'] = str(comm_msg_info.get('type', ''))
            if item['type'] == '1':
                # 文字
                item['content'] = comm_msg_info.get('content', '')
            elif item['type'] == '3':
                # 图片
                item[
                    'img_url'] = 'https://mp.weixin.qq.com/mp/getmediadata?__biz=' + biz + '&type=img&mode=small&msgid=' + \
                                 str(item['qunfa_id']) + '&uin=' + uin + '&key=' + key
            elif item['type'] == '34':
                # 音频
                item['play_length'] = listdic['voice_msg_ext_info'].get('play_length', '')
                item['fileid'] = listdic['voice_msg_ext_info'].get('fileid', '')
                item['audio_src'] = 'https://mp.weixin.qq.com/mp/getmediadata?__biz=' + biz + '&type=voice&msgid=' + \
                                    str(item['qunfa_id']) + '&uin=' + uin + '&key=' + key
            elif item['type'] == '49':
                # 图文
                app_msg_ext_info = listdic['app_msg_ext_info']
                url = app_msg_ext_info.get('content_url')
                if url:
                    url = 'http://mp.weixin.qq.com' + url if 'http://mp.weixin.qq.com' not in url else url
                else:
                    url = ''
                msg_index = 1
                item['main'] = msg_index
                item['title'] = app_msg_ext_info.get('title', '')
                item['digest'] = app_msg_ext_info.get('digest', '')
                item['fileid'] = app_msg_ext_info.get('fileid', '')
                item['content_url'] = url
                item['source_url'] = app_msg_ext_info.get('source_url', '')
                item['cover'] = app_msg_ext_info.get('cover', '')
                item['author'] = app_msg_ext_info.get('author', '')
                item['copyright_stat'] = app_msg_ext_info.get('copyright_stat', '')
                items.append(item)
                if app_msg_ext_info.get('is_multi', 0) == 1:
                    for multidic in app_msg_ext_info['multi_app_msg_item_list']:
                        url = multidic.get('content_url')
                        if url:
                            url = 'http://mp.weixin.qq.com' + url if 'http://mp.weixin.qq.com' not in url else url
                        else:
                            url = ''
                        itemnew = dict()
                        itemnew['qunfa_id'] = item['qunfa_id']
                        itemnew['datetime'] = item['datetime']
                        itemnew['type'] = item['type']
                        msg_index += 1
                        itemnew['main'] = msg_index
                        itemnew['title'] = multidic.get('title', '')
                        itemnew['digest'] = multidic.get('digest', '')
                        itemnew['fileid'] = multidic.get('fileid', '')
                        itemnew['content_url'] = url
                        itemnew['source_url'] = multidic.get('source_url', '')
                        itemnew['cover'] = multidic.get('cover', '')
                        itemnew['author'] = multidic.get('author', '')
                        itemnew['copyright_stat'] = multidic.get('copyright_stat', '')
                        items.append(itemnew)
                continue
            elif item['type'] == '62':
                item['cdn_videoid'] = listdic['video_msg_ext_info'].get('cdn_videoid', '')
                item['thumb'] = listdic['video_msg_ext_info'].get('thumb', '')
                item['video_src'] = 'https://mp.weixin.qq.com/mp/getcdnvideourl?__biz=' + biz + '&cdn_videoid=' + item[
                    'cdn_videoid'] + '&thumb=' + item['thumb'] + '&uin=' + uin + '&key=' + key
            items.append(item)
        return items

    def _get_gzh_article_text(self, url):
        """获取文章文本

        Args:
            url: 文章链接

        Returns:
            text: 文章文本
        """
        return self._get(url, 'get', host='mp.weixin.qq.com')

    def _deal_related(self, url, title):
        """获取文章相似文章

        Args:
            url: 文章链接
            title: 文章标题

        Returns:
            related_dict: 相似文章字典

        Raises:
            WechatSogouException: 错误信息errmsg
        """
        related_req_url = 'http://mp.weixin.qq.com/mp/getrelatedmsg?' \
                          'url=' + quote(url) \
                          + '&title=' + title \
                          + '&uin=&key=&pass_ticket=&wxtoken=&devicetype=&clientversion=0&x5=0'
        related_text = self._get(related_req_url, 'get', host='mp.weixin.qq.com', referer=url)
        related_dict = eval(related_text)
        ret = related_dict['base_resp']['ret']
        errmsg = related_dict['base_resp']['errmsg'] if related_dict['base_resp']['errmsg'] else 'ret:' + str(ret)
        if ret != 0:
            #logger.error(errmsg)
            raise WechatSogouException(errmsg)
        return related_dict

    def _uinkeybiz(self, keyword, uin=None, key=None, biz=None, pass_ticket=None, msgid=None):
        if uin:
            self._cache.set(keyword + 'uin', uin, 36000)
            self._cache.set(keyword + 'key', key, 36000)
            self._cache.set(keyword + 'biz', biz, 36000)
            self._cache.set(keyword + 'pass_ticket', pass_ticket, 36000)
            self._cache.set(keyword + 'msgid', msgid, 36000)
        else:
            uin = self._cache.get(keyword + 'uin')
            key = self._cache.get(keyword + 'key')
            biz = self._cache.get(keyword + 'biz')
            pass_ticket = self._cache.get(keyword + 'pass_ticket')
            msgid = self._cache.get(keyword + 'msgid')
            return uin, key, biz, pass_ticket, msgid

    def _cache_history_session(self, keyword, session=None):
        if session:
            self._cache.set(keyword + 'session', session, 36000)
        else:
            return self._cache.get(keyword + 'session')
