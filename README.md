基于搜狗微信搜索的微信公众号爬虫
===


![py27](https://camo.githubusercontent.com/392a32588691a8418368a51ff33a12d41f11f0a9/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f707974686f6e2d322e372d6666363962342e737667)

2019-03-07 增加对py3的支持，同时支持py2和py3

2017-4-27搜狗微信取消了阅读、点攒及评论数据，所以无法通过搜狗获取这些数据了，有需要的可以联系我
恰谈代抓业务，按量计费，扣扣：3221449010

# 项目简介
基于搜狗微信搜索的微信公众号爬虫
可以抓取指定公众号的文章信息

# 赞助作者
俺是自由职业者，好汉们如果可能的话赞助一些让俺将开源事业进行到底，谢谢！！！

<img src="https://github.com/jaryee/wechat_sogou_crawl/blob/master/screenshot/wx.png" width="250" />
<img src="https://github.com/jaryee/wechat_sogou_crawl/blob/master/screenshot/zfb.png" width="250" />

兄弟我弄了个淘宝店，有时间的兄弟给捧个场啊，新店需要信誉积分，跪谢！只要一块钱，就能温暖你我他
https://item.taobao.com/item.htm?spm=a230r.1.14.16.PRhaio&id=543333631871&ns=1&abbucket=6#detail



使用教程大家可以去我的微博查看：
http://blog.csdn.net/niuxiaojia09/article/details/55260770

如果有问题，请提issue，或者发邮件到：jaryee@163.com联系我

新建QQ群：482588657  有兴趣同学可以进来一起讨论

2017-1-20 增加如何使程序进入搜狗微信登录状态的说明，在Updatemp.py和UpdateWenzhang.py中都有操作说明
2017-3-21 在API.py中增加把文章本地化的函数，可以根据自己的需要把文章下载到本地

# 项目使用

一、使用说明

1、在mysql数据库中创建数据库，数据库命名为Jubang,数据格式为utf8mb4，然后导入jubang.sql文件，创建对应的数据库表

2、修改config.py文件中对应的设置，打码平台配置ruokuai这个一定要设置，否则出现验证码就不能正常工作了

3、执行：pip install -r requirements.txt  安装所需要的第三方包

4、手动或自动在add_mp_list表中增加数据，然后运行auto_add_mp.py文件。
   比如可以这样用：给auto_add_mp.py设定一个定时任务，5分钟或10分钟，然后前台页面文件让使用者添加待抓取的
   公众号信息，然后定时任务执行时就可以把这些公众号加入待抓取列表了
   add_mp_list中
   name字段是模糊抓取，会根据输入的名称模糊加入10个公众号
   wx_hao字段是精确抓取，这个是公众号的微信号，只抓取一个
   这两个字段可以任意填入一个就行

5、执行updatemp.py文件，文件说明看后面。使用中可以给该文件设定定时任务30分钟或其它间隔，每隔一定时间，运行该
   文件就会抓取已添加的公众号是否有新文章发出来。
   第一次使用会抓取公众号的最近10条群发数据

6、执行updatewenzhang.py文件，该文件是抓取文章阅读及点攒数的。最新的数据会写入wenzhang_info表中，并且会在表wenzhang_statistics中
   添加增量记录，可以根据wenzhang_statistics表中的数据生成曲线图
   使用中可以给该文件添加5分钟或其它时间的定时任务，这样就可以来生成对应的阅读曲线图了

二、文件说明

1、updatemp.py
该文件遍历待抓取列表（数据库表：mp_info），查询表中的公众号是否有新文章发布，如果有，就抓取新的文章信息并
放入数据库表wenzhang_info中

2、updatewenzhang.py
该文件遍历文章表，然后抓取24小时之内的文章阅读数据存入表wenzhang_info和表wenzhang_statistics中

3、 auto_add_mp.py
该文件将指定的公众号添加到待抓取列表中
该文件读取数据库表（add_mp_list）中的内容，然后将其中指定的公众号填入数据库表（mp_info）中



# TODO
- [x] 使用py2.7
- [x] 获取指定公众号文章
- [x] 文章详情页信息
- [x] 验证码自动识别

---