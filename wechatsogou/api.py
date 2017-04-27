# -*- coding: utf-8 -*-

import re
import requests
import time
from lxml import etree
from wechatsogou.tools import *
from .basic import WechatSogouBasic
from .exceptions import *
import json
import logging
import urlparse
import urllib2
import httplib2
import codecs,os
from bs4 import BeautifulSoup
logger = logging.getLogger()


class WechatSogouApi(WechatSogouBasic):
    """基于搜狗搜索的的微信公众号爬虫接口  接口类
    """

    def __init__(self, **kwargs):
        super(WechatSogouApi, self).__init__(**kwargs)

    def search_gzh_info(self, name, page=1):
        """搜索公众号

        Args:
            name: 搜索关键字
            page: 搜索的页数

        Returns:
            列表，每一项均是{'name':name,'wechatid':wechatid,'jieshao':jieshao,'renzhen':renzhen,'qrcode':qrcodes,'img':img,'url':url}
            name: 公众号名称
            wechatid: 公众号id
            jieshao: 介绍
            renzhen: 认证，为空表示未认证
            qrcode: 二维码 暂无
            img: 头像图片
            url: 文章地址
            last_url: 最后一篇文章地址 暂无
        """
        text = self._search_gzh_text(name, page)
        
        try:
            page = etree.HTML(text)
        except:
            return ""

        img = list()
        #头像
        info_imgs = page.xpath(u"//div[@class='img-box']//img")
        for info_img in info_imgs:
            img.append(info_img.attrib['src'])
        #文章列表
        url = list()
        info_urls = page.xpath(u"//div[@class='img-box']//a");
        for info_url in info_urls:
            url.append(info_url.attrib['href'])
        
        #微信号
        wechatid = page.xpath(u"//label[@name='em_weixinhao']/text()");

        #公众号名称
        name = list()
        name_list = page.xpath(u"//div[@class='txt-box']/p/a")
        for name_item in name_list:
            name.append(name_item.xpath('string(.)'))
       
        last_url = list()
        jieshao = list()
        renzhen = list()
        list_index = 0
        #介绍、认证、最近文章
        info_instructions = page.xpath(u"//ul[@class='news-list2']/li")
        for info_instruction in info_instructions:
            cache = self._get_elem_text(info_instruction)
            cache = cache.replace('red_beg', '').replace('red_end', '')
            cache_list = cache.split('\n')
            cache_re = re.split(u'功能介绍：|认证：|最近文章：', cache_list[0])
            if(cache.find("最近文章") == -1) :
                last_url.insert(list_index,"")
            list_index += 1

            if(len(cache_re) > 1):
                jieshao.append(re.sub("document.write\(authname\('[0-9]'\)\)", "", cache_re[1]))
                if "authname" in cache_re[1]:
                    renzhen.append(cache_re[2])
                else:
                    renzhen.append('')
            else:
                #没取到，都为空吧
                jieshao.append('')
                renzhen.append('')

        returns = list()
        for i in range(len(name)):
            returns.append(
                {
                    'name': name[i],
                    'wechatid': wechatid[i],
                    'jieshao': jieshao[i],
                    'renzhen': renzhen[i],
                    'qrcode': '',
                    'img': img[i],
                    'url': url[i],
                    'last_url': ''
                }
            )
        return returns

    def get_gzh_info(self, wechatid):
        """获取公众号微信号wechatid的信息

        因为wechatid唯一确定，所以第一个就是要搜索的公众号

        Args:
            wechatid: 公众号id

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
        try:
            info = self.search_gzh_info(wechatid, 1)
            return info[0] if info else False
        except:
            return ""


    def search_article_info(self, name, page=1):
        """搜索文章

        Args:
            name: 搜索文章关键字
            page: 搜索的页数

        Returns:
            列表，每一项均是{'name','url','img','zhaiyao','gzhname','gzhqrcodes','gzhurl','time'}
            name: 文章标题
            url: 文章链接
            img: 文章封面图片缩略图，可转为高清大图
            zhaiyao: 文章摘要
            time: 文章推送时间，10位时间戳
            gzhname: 公众号名称
            gzhqrcodes: 公众号二维码
            gzhurl: 公众号最近文章地址
            page_count:共有多少页

        """
        text = self._search_article_text(name, page)
        text = text.replace("amp;","")
        page = etree.HTML(text)
        #搜索到的总条数
        page_count = page.xpath(u"//div[@class='mun']/text()")
        page_count = page_count[0].replace(',','').replace('找到约','').replace('条结果','')

        #文章信息
        zhaiyao = list()
        #摘要
        zhaiyao_list = page.xpath(u"//ul[@class='news-list']/li//p[@class='txt-info']")
        for zhaiyao_item in zhaiyao_list:
            zhaiyao.append(zhaiyao_item.xpath('string(.)'))
        
        #标题
        name = list()
        info_names = page.xpath(u"//div[@class='txt-box']/h3/a")
        for info_name in info_names:
            name.append(info_name.xpath('string(.)'))
        
        #公众号名称
        gzhname = list()
        gzhwxhao = list()
        gzhqrcodes = list()
        gzhurl = list()
        info_gzhs = page.xpath(u"//div[@class='txt-box']/div[@class='s-p']/a")
        for info_gzh in info_gzhs:
            #gzhname.append(info_gzh.attrib['data-sourcename'])
            #gzhwxhao.append(info_gzh.attrib['data-username'])
            #gzhqrcodes.append(info_gzh.attrib['data-encqrcodeurl'])
            gzhurl.append(info_gzh.attrib['href'])

        #文章URL
        url = list()
        info_urls = page.xpath(u"//div[@class='txt-box']/h3/a")
        for info_url in info_urls:
            url.append(info_url.attrib['href'])
        
        #文章时间
        time = list()
        info_times = page.xpath(u"//div[@class='txt-box']/div[@class='s-p']")
        for info_time in info_times:
            time.append(info_time.attrib['t'])

        #封面
        img = list()
        info_imgs = page.xpath(u"//ul[@class='news-list']/li")
        for info_img in info_imgs:
            img_box = info_img.xpath(u"div[@class='img-box']/a/img")
            if len(img_box) > 0 :
                #普通封面的
                img.append(img_box[0].attrib['src'])
            else:
                #3张封面的
                img_box = info_img.xpath(u"div[@class='txt-box']/div[@class='img-d']/a/span/img")
                if len(img_box) > 0 :
                    #拿第一个
                    img.append(img_box[0].attrib['src'])
                else:
                    #没拿到
                    img.append("")

        returns = list()
        for i in range(len(url)):
            returns.append(
                {
                    'name': name[i],
                    'url': url[i],
                    'img': img[i],
                    'zhaiyao': zhaiyao[i],
                    'gzhname': list_or_empty(gzhname),
                    'gzhqrcodes': list_or_empty(gzhqrcodes),
                    'gzhurl': gzhurl[i],
                    'time': time[i],
                    'page_count':int(page_count)
                }
            )
        return returns

    def get_gzh_message(self, **kwargs):
        """解析最近文章页  或  解析历史消息记录

        Args:
            ::param url 最近文章地址
            ::param wechatid 微信号
            ::param wechat_name 微信昵称(不推荐，因为不唯一)

            最保险的做法是提供url或者wechatid

        Returns:
            gzh_messages 是 列表，每一项均是字典，一定含有字段qunfa_id,datetime,type
            当type不同时，含有不同的字段，具体见文档
        """
        url = kwargs.get('url', None)
        wechatid = kwargs.get('wechatid', None)
        wechat_name = kwargs.get('wechat_name', None)
        if url:
            text = self._get_gzh_article_by_url_text(url)
        elif wechatid:
            gzh_info = self.get_gzh_info(wechatid)
            url = gzh_info['url']
            text = self._get_gzh_article_by_url_text(url)
        elif wechat_name:
            gzh_info = self.get_gzh_info(wechat_name)
            url = gzh_info['url']
            text = self._get_gzh_article_by_url_text(url)
        else:
            raise WechatSogouException('get_gzh_recent_info need param text and url')
        
        if u'链接已过期' in text:
            return '链接已过期'
        return self._deal_gzh_article_dict(self._get_gzh_article_by_url_dict(text))

    def get_gzh_message_and_info(self, **kwargs):
        """最近文章页  公众号信息 和 群发信息

        Args:
            ::param url 最近文章地址
            ::param wechatid 微信号
            ::param wechat_name 微信昵称(不推荐，因为不唯一)

            最保险的做法是提供url或者wechatid

        Returns:
            字典{'gzh_info':gzh_info, 'gzh_messages':gzh_messages}

            gzh_info 也是字典{'name':name,'wechatid':wechatid,'jieshao':jieshao,'renzhen':renzhen,'qrcode':qrcodes,'img':img,'url':url}
            name: 公众号名称
            wechatid: 公众号id
            jieshao: 介绍
            renzhen: 认证，为空表示未认证
            qrcode: 二维码
            img: 头像图片
            url: 最近文章地址

            gzh_messages 是 列表，每一项均是字典，一定含有字段qunfa_id,datetime,type
            当type不同时，含有不同的字段，具体见文档
        """
        url = kwargs.get('url', None)
        wechatid = kwargs.get('wechatid', None)
        wechat_name = kwargs.get('wechat_name', None)
        if url:
            text = self._get_gzh_article_by_url_text(url)
        elif wechatid:
            gzh_info = self.get_gzh_info(wechatid)
            url = gzh_info['url']
            text = self._get_gzh_article_by_url_text(url)
        elif wechat_name:
            gzh_info = self.get_gzh_info(wechat_name)
            url = gzh_info['url']
            text = self._get_gzh_article_by_url_text(url)
        else:
            raise WechatSogouException('get_gzh_recent_info need param text and url')

        return {
            'gzh_info': self._get_gzh_article_gzh_by_url_dict(text, url),
            'gzh_messages': self._deal_gzh_article_dict(self._get_gzh_article_by_url_dict(text))
        }

    def deal_article_content(self, **kwargs):
        """获取文章内容

        Args:
            ::param url 文章页 url
            ::param text 文章页 文本

        Returns:
            content_html, content_rich, content_text
            content_html: 原始文章内容，包括html标签及样式
            content_rich: 包含图片（包括图片应展示的样式）的文章内容
            content_text: 包含图片（`<img src="..." />`格式）的文章内容
        """
        url = kwargs.get('url', None)
        text = kwargs.get('text', None)

        if text:
            pass
        elif url:
            text = self._get_gzh_article_text(url)
        else:
            raise WechatSogouException('deal_content need param url or text')

        bsObj = BeautifulSoup(text)
        content_text = bsObj.find("div", {"class":"rich_media_content", "id":"js_content"})
        content_html = content_text.get_text()
        # content_html = re.findall(u'<div class="rich_media_content " id="js_content">(.*?)</div>', text, re.S)
        # if content_html :
        #     content_html = content_html[0]

        # content_rich = re.sub(u'<(?!img|br).*?>', '', content_html)
        # pipei = re.compile(u'<img(.*?)src="(.*?)"(.*?)/>')
        # content_text = pipei.sub(lambda m: '<img src="' + m.group(2) + '" />', content_rich)
        return content_html

    def deal_article_related(self, url, title):
        """获取文章相似文章

        Args:
            url: 文章链接
            title: 文章标题

        Returns:
            related_dict: 相似文章字典

        Raises:
            WechatSogouException: 错误信息errmsg
        """
        return self._deal_related(url, title)

    def deal_article_comment(self, **kwargs):
        """获取文章评论

        Args:
            text: 文章文本

        Returns:
            comment_dict: 评论字典

        Raises:
            WechatSogouException: 错误信息errmsg
        """
        url = kwargs.get('url', None)
        text = kwargs.get('text', None)

        if text:
            pass
        elif url:
            text = self._get_gzh_article_text(url)
        else:
            raise WechatSogouException('deal_content need param url or text')

        sg_data = re.findall(u'window.sg_data={(.*?)}', text, re.S)
        if not sg_data :
            return ""
        sg_data = '{' + sg_data[0].replace(u'\r\n', '').replace(' ', '') + '}'
        sg_data = re.findall(u'{src:"(.*?)",ver:"(.*?)",timestamp:"(.*?)",signature:"(.*?)"}', sg_data)[0]
        comment_req_url = 'http://mp.weixin.qq.com/mp/getcomment?src=' + sg_data[0] + '&ver=' + sg_data[
            1] + '&timestamp=' + sg_data[2] + '&signature=' + sg_data[
                              3] + '&uin=&key=&pass_ticket=&wxtoken=&devicetype=&clientversion=0&x5=0'
        comment_text = self._get(comment_req_url, 'get', host='mp.weixin.qq.com', referer='http://mp.weixin.qq.com')
        comment_dict = eval(comment_text)
        ret = comment_dict['base_resp']['ret']
        errmsg = comment_dict['base_resp']['errmsg'] if comment_dict['base_resp']['errmsg'] else 'ret:' + str(ret)
        if ret != 0:
            logger.error(errmsg)
            raise WechatSogouException(errmsg)
        return comment_dict

    def deal_article_yuan(self, **kwargs):
        url = kwargs.get('url', None)
        text = kwargs.get('text', None)

        if text:
            pass
        elif url:
            text = self._get_gzh_article_text(url)
        else:
            raise WechatSogouException('deal_article_yuan need param url or text')
        try:
            yuan = re.findall('var msg_link = "(.*?)";', text)[0].replace('amp;', '')
        except IndexError as e:
            if '系统出错' not in text:
                logger.error(e)
                print(e)
                print(text)

            raise WechatSogouBreakException()
        return yuan

    def deal_article(self, url, title=None):
        """获取文章详情

        Args:
            url: 文章链接
            title: 文章标题
            注意，title可以为空，则表示不根据title获取相似文章

        Returns:
            {'yuan':'','related':'','comment':'','content': {'content_html':'','content_rich':'','content_text':''}
            yuan: 文章固定地址
            related: 相似文章信息字典
            comment: 评论信息字典
            content: 文章内容
        """
        text = self._get_gzh_article_text(url)
        
        yuan_url = self.deal_get_real_url(url)

        comment = '' #2017-04-27搜狗微信取消评论数据self.deal_article_comment(text=text)
        content_html = self.deal_article_content(text=text)
        retu = {
            'yuan': yuan_url,
            'comment': comment,
            'content_html': content_html
        }

        if title is not None:
            related = self.deal_article_related(url, title)
            retu['related'] = related
            return retu
        else:
            return retu

    def get_recent_article_url_by_index_single(self, kind=0, page=0):
        """获取首页推荐文章公众号最近文章地址

        Args:
            kind: 类别，从0开始，经检测，至少应检查0-19，不保证之间每个都有
            page: 页数，从0开始

        Returns:
            recent_article_urls或者False
            recent_article_urls: 最近文章地址列表
            False: 该kind和page对应的页数没有文章
        """
        if page == 0:
            page_str = 'pc_0'
        else:
            page_str = str(page)
        url = 'http://weixin.sogou.com/pcindex/pc/pc_' + str(kind) + '/' + page_str + '.html'
        try:
            text = self._get(url)
            page = etree.HTML(text)
            recent_article_urls = page.xpath('//li/div[@class="pos-wxrw"]/a/@href')
            reurls = []
            for reurl in recent_article_urls:
                if 'mp.weixin.qq.com' in reurl:
                    reurls.append(reurl)
            return reurls
        except WechatSogouRequestsException as e:
            if e.status_code == 404:
                return False

    def get_recent_article_url_by_index_all(self):
        """获取首页推荐文章公众号最近文章地址，所有分类，所有页数

        Returns:
            return_urls: 最近文章地址列表
        """
        return_urls = []
        for i in range(20):
            j = 0
            urls = self.get_recent_article_url_by_index_single(i, j)
            while urls:
                return_urls.extend(urls)
                j += 1
                urls = self.get_recent_article_url_by_index_single(i, j)
        return return_urls

    def get_sugg(self, keyword):
        """获取微信搜狗搜索关键词联想

        Args:
            keyword: 关键词

        Returns:
            sugg: 联想关键词列表

        Raises:
            WechatSogouException: get_sugg keyword error 关键词不是str或者不是可以str()的类型
            WechatSogouException: sugg refind error 返回分析错误
        """
        try:
            keyword = str(keyword) if type(keyword) != str else keyword
        except Exception as e:
            logger.error('get_sugg keyword error', e)
            raise WechatSogouException('get_sugg keyword error')
        url = 'http://w.sugg.sogou.com/sugg/ajaj_json.jsp?key=' + keyword + '&type=wxpub&pr=web'
        text = self._get(url, 'get', host='w.sugg.sogou.com')
        try:
            sugg = re.findall(u'\["' + keyword + '",(.*?),\["', text)[0]
            sugg = eval(sugg)
            return sugg
        except Exception as e:
            logger.error('sugg refind error', e)
            raise WechatSogouException('sugg refind error')

    def deal_mass_send_msg(self, url, wechatid):
        """解析 历史消息

        ::param url是抓包获取的历史消息页
        """
        session = requests.session()
        r = session.get(url, verify=False)
        #print(r)
        if r.status_code == requests.codes.ok:
            try:
                biz = re.findall('biz = \'(.*?)\',', r.text)[0]
                key = re.findall('key = \'(.*?)\',', r.text)[0]
                uin = re.findall('uin = \'(.*?)\',', r.text)[0]
                pass_ticket = self._get_url_param(url).get('pass_ticket', [''])[0]

                self._uinkeybiz(wechatid, uin, key, biz, pass_ticket, 0)
                self._cache_history_session(wechatid, session)

            except IndexError:
                logger.error('deal_mass_send_msg error. maybe you should get the mp url again')
                #raise WechatSogouHistoryMsgException('deal_mass_send_msg error. maybe you should get the mp url again')
                return 404
        else:
            logger.error('requests status_code error', r.status_code)
            raise WechatSogouRequestsException('requests status_code error', r.status_code)

    #获取历史消息
    def deal_mass_send_msg_page(self, wechatid, updatecache=True):
        url = 'http://mp.weixin.qq.com/mp/getmasssendmsg?'
        uin, key, biz, pass_ticket, frommsgid = self._uinkeybiz(wechatid)
        #print([uin, key, biz, pass_ticket, frommsgid])
        url = url + 'uin=' + uin + '&'
        url = url + 'key=' + key + '&'
        url = url + '__biz=' + biz + '&'
        url = url + 'pass_ticket=' + pass_ticket + '&'
        url = url + 'frommsgid=' + str(frommsgid) + '&'
        data = {
            'f': 'json',
            'count': '10',
            'wxtoken': '',
            'x5': '0'
        }
        for k, v in data.items():
            url = url + k + '=' + v + '&'
        url = url[:-1]
        # print(url)

        try:
            session = self._cache_history_session(wechatid)
            r = session.get(url, headers={'Host': 'mp.weixin.qq.com'}, verify=False)
            #print(r.text)
            rdic = eval(r.text)
            if rdic['ret'] == 0:

                data_dict_from_str = self._str_to_dict(rdic['general_msg_list'])

                if rdic['is_continue'] == 0 and rdic['count'] == 0:
                    raise WechatSogouEndException()

                msg_dict = self._deal_gzh_article_dict(data_dict_from_str)
                msg_dict_new = reversed(msg_dict)
                msgid = 0
                for m in msg_dict_new:
                    if int(m['type']) == 49:
                        msgid = m['qunfa_id']
                        break

                if updatecache:
                    self._uinkeybiz(wechatid, rdic['uin_code'], rdic['key'], rdic['bizuin_code'], pass_ticket, msgid)

                return msg_dict
            else:
                logger.error('deal_mass_send_msg_page ret ' + str(rdic['ret']) + ' errmsg ' + rdic['errmsg'])
                raise WechatSogouHistoryMsgException(
                    'deal_mass_send_msg_page ret ' + str(rdic['ret']) + ' errmsg ' + rdic['errmsg'])
        except AttributeError:
            logger.error('deal_mass_send_msg_page error, please delete cache file')
            raise WechatSogouHistoryMsgException('deal_mass_send_msg_page error, please delete cache file')


    #获取阅读数据
    def deal_get_fwh_read(self, wechatid, updatecache,**kwargs):
        url = 'http://mp.weixin.qq.com/mp/getappmsgext?'
        uin, key, biz, pass_ticket, frommsgid = self._uinkeybiz(wechatid)
        #print([uin, key, biz, pass_ticket, frommsgid])
        url = url + 'uin=' + uin + '&'
        url = url + 'key=' + key + '&'
        url = url + '__biz=' + biz + '&'
        url = url + 'pass_ticket=' + pass_ticket + '&'
        url = url + 'frommsgid=' + str(frommsgid) + '&'
        url = url + 'mid=' + kwargs.get('mid', None) + '&'
        url = url + 'sn=' + kwargs.get('sn', None) + '&'
        url = url + 'idx=' + kwargs.get('idx', None) + '&'

        data = {
            'f': 'json',
            'count': '10',
            'wxtoken': '',
            'x5': '0'
        }
        for k, v in data.items():
            url = url + k + '=' + v + '&'
        url = url[:-1]
        # print(url)

        try:
            session = self._cache_history_session(wechatid)
            print(url)
            r = session.post(url,headers={'Host': 'mp.weixin.qq.com',
                                          'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 MicroMessenger/6.5.2.501 NetType/WIFI WindowsWechat'},
                                          data={'is_only_read':1}, verify=False)
            

            if r.status_code == requests.codes.ok:
                try:
                    rdic = json.loads(r.text)
                    return rdic['appmsgstat']
                    
                except IndexError:
                    logger.error('deal_mass_send_msg error. maybe you should get the mp url again')
                    #raise WechatSogouHistoryMsgException('deal_mass_send_msg error. maybe you should get the mp url again')
                    return 404
            else :
                logger.error('requests status_code error', r.status_code)
                raise WechatSogouRequestsException('requests status_code error', r.status_code)

        except AttributeError:
            logger.error('deal_mass_send_msg_page error, please delete cache file')
            raise WechatSogouHistoryMsgException('deal_mass_send_msg_page error, please delete cache file')

    #获取搜狗微信文章上的真实链接
    def deal_get_real_url(self, url):
        try:
            url = url + '&uin=MjExMTY2MjUzNg=='
            text = requests.get(url,allow_redirects=False)
            return text.headers['Location']
        except:
            return ""

    #下载文章到本地
    def down_html(self, url,dir_name):
        try:
            #获取biz
            params =  urlparse.urlsplit(url).query
            params = urlparse.parse_qs(params,True)
            if not params.has_key('__biz') :
                #可能是搜狗链接，先转成微信连接
                url = self.deal_get_real_url(url)

            url = url.replace('\\x26','&')
            url = url.replace('x26','&')

            print(url)
            h = httplib2.Http(timeout=30)
            html = self._get_gzh_article_text(url)
            content = html

            # 正则表达式javascript里的获取相关变量
            ct = re.findall('var ct = "(.*?)";', content)[0]
            msg_cdn_url = re.findall('var msg_cdn_url = "(.*?)";', content)[0]
            nickname = re.findall('var nickname = "(.*?)";', content)[0]
            if(nickname == ""):
                nickname = "not has name"
            if(ct == ""):
                ct = time.time()

            ctime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(ct))) # int将字符串转成数字，不区分int和long, 这里将时间秒数转成日期格式
            # 建立文件夹
            #编码转换
            if isinstance(dir_name, unicode): 
                dir_name = dir_name.encode('GB18030','ignore')
            else: 
                dir_name = dir_name.decode('utf-8','ignore').encode('GB18030','ignore')
            
            #print 
            if isinstance(nickname, unicode): 
                nickname = nickname.encode('GB18030','ignore')
            else: 
                if chardet.detect(nickname)['encoding'] == 'KOI8-R' :
                    print("KOI8")
                    nickname = nickname.decode('KOI8-R','ignore').encode('GB18030','ignore')
                else:
                    print("GB18030")
                    nickname = nickname.decode('utf-8','ignore').encode('GB18030','ignore')

            dir = 'WeiXinGZH/' + nickname + '/' + ctime + '/' + dir_name + '/'
            #dir = 'WeiXinGZH/' + dir_name + '/'
            dir = dir.decode('gb2312','ignore')
            dir = dir.replace("?", "")
            dir = dir.replace("\\", "")
            dir = dir.replace("*", "")
            dir = dir.replace(":", "")
            dir = dir.replace('\"', "")
            dir = dir.replace("<", "")
            dir = dir.replace(">", "")
            dir = dir.replace("|", "")


            try :
                os.makedirs(dir)  # 建立相应的文件夹
                
            except :
                #不处理
                errormsg = 'none'

            # 下载封面
            url = msg_cdn_url
            print u'正在下载文章：' + url
            resp, contentface = h.request(url)
            
            file_name = dir + 'cover.jpg'
            codecs.open(file_name,mode='wb').write(contentface)

            # 下载其他图片
            soup = BeautifulSoup(content, 'html.parser')
            count = 0
            #logger.error(html)
            err_count = 0
            for link in soup.find_all('img') :
                try:
                    err_count += 1
                    if(err_count > 200) :
                        break #防止陷阱

                    if None != link.get('data-src') :
                        count = count + 1
                        orurl = link.get('data-src')
                        url = orurl.split('?')[0]  # 重新构造url，原来的url有一部分无法下载
                        #print u'正在下载：' + url
                        resp, content = h.request(url)

                        matchurlvalue = re.search(r'wx_fmt=(?P<wx_fmt>[^&]*)', orurl) # 无参数的可能是gif，也有可能是jpg
                        if None != matchurlvalue:
                            wx_fmt = matchurlvalue.group('wx_fmt') # 优先通过wx_fmt参数的值判断文件类型
                        else:
                            wx_fmt = binascii.b2a_hex(content[0:4]) # 读取前4字节转化为16进制字符串

                        #print wx_fmt
                        phototype = { 'jpeg': '.jpg', 'gif' : '.gif', 'png' : '.png', 'jpg' : '.jpg', '47494638' : '.gif', 'ffd8ffe0' : '.jpg', 'ffd8ffe1' : '.jpg', 'ffd8ffdb' : '.jpg', 'ffd8fffe' : '.jpg', 'other' : '.jpg', '89504e47' : '.png' }  # 方便写文件格式
                        file_name = 'Picture' + str(count) + phototype[wx_fmt]
                        file_path = dir + file_name
                        open(file_path, 'wb').write(content)

                        #图片替换成本地地址
                        re_url = 'data-src="%s(.+?)"' % (url[:-5])
                        re_pic = 'src="%s"' % (file_name)
                        html = re.sub(re_url, re_pic, html)
                except:
                    continue

            with open("%sindex.html" % (dir), "wb") as code :
                code.write(html)

            print u'文章下载完成'
            ret_path = os.path.abspath('.')
            ret_path = ret_path.replace('\\', "/")
            ret_path = "%s/%sindex.html" %(ret_path.decode('GB18030').encode('utf-8'),dir)
            #print(ret_path)
        #except:
        except WechatSogouHistoryMsgException:
            print u'文章内容有异常编码，无法下载'
            return ""
        return ret_path


