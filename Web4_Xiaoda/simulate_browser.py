import os
from selenium import webdriver
from pyquery import PyQuery as pq
import random

driver = webdriver.PhantomJS()

'''
组成部分
    1. Downloader 下载页面          浏览器  PhantomJS
    2. HTMLParser 解析页面          pyquery     lxml
    3. DataModel 字段 - element     业务逻辑
'''

'''
编码
00011110001111 32bit
127

1. 二进制表示
2. 字符串表示

字符 -> 二进制

ascii english number roma
unicode
    utf-8   1, 2, 3, 4
    utf-16  2，4
    utf-32  4

gbk 字符很少
gb18030 百度最终都会转成这个

考虑任何东西的时候，都有一个编码
1. console
2. file
3. editor
'''

# 引入配置对象DesiredCapabilities
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

dcap = dict(DesiredCapabilities.PHANTOMJS)
# 从USER_AGENTS列表中随机选一个浏览器头，伪装浏览器
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36',
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/53 (KHTML, like Gecko) Chrome/15.0.87"
]
dcap["phantomjs.page.settings.userAgent"] = (random.choice(USER_AGENTS))
# 不载入图片，爬页面速度会快很多
dcap["phantomjs.page.settings.loadImages"] = False
# 设置代理
service_args = ['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1']
# service_args = ['--proxy=127.0.0.1:9999', '--proxy-type=socks5']

# 打开带配置信息的 phantomJS 浏览器
driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=service_args)
# 隐式等待5秒，可以自己调节
driver.implicitly_wait(10)
# 设置10秒页面超时返回，类似于requests.get()的timeout选项，driver.get()没有timeout选项
# 以前遇到过driver.get(url)一直不返回，但也不报错的问题，这时程序会卡住，设置超时选项能解决这个问题。
driver.set_page_load_timeout(90)
# 设置10秒脚本超时时间
driver.set_script_timeout(90)


class Model(object):
    """
    基类, 用来显示类的信息
    """

    def __repr__(self):
        name = self.__class__.__name__
        properties = ('{}=({})'.format(k, v) for k, v in self.__dict__.items())
        s = '\n<{} \n  {}>'.format(name, '\n  '.join(properties))
        return s


class RecommendItem(Model):
    """
    存储推荐商品信息
    """

    def __init__(self):
        self.title = ''
        self.cover_url = ''
        self.abstract = ''


def cached_url(url):
    """
    缓存, 避免重复下载网页浪费时间
    """
    folder = 'cached_zh'
    filename = url.rsplit('/')[-2] + '.html'
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            s = f.read()
            return s
    else:
        # 建立 cached 文件夹
        if not os.path.exists(folder):
            os.makedirs(folder)

        driver.get(url)
        #    return driver.page_source
        #    return driver.page_source
        with open(path, 'wb') as f:
            f.write(driver.page_source.encode())
        content = driver.page_source
        return content


def item_from_div(div):
    """
    从一个 div 里面获取到一个电影信息
    """
    e = pq(div)

    # 小作用域变量用单字符
    m = RecommendItem()
    m.abstract = e(".post_box_main .text").text()
    m.name = e(".title_box a").text()
    m.cover_url = e('.post_box_img img').attr('src')
    return m


def item_from_url(url):
    """
    从 url 中下载网页并解析出页面内所有的电影
    """
    page = cached_url(url)
    e = pq(page)
    items = e(".post_box")
    return [item_from_div(i) for i in items]


def main():
    items = item_from_url('http://zhizhizhi.com/gn/1/')
    for i in range(0, 10):
        items = item_from_url("http://zhizhizhi.com/gn/{}/".format(i))
        print(items)
    driver.close()


if __name__ == '__main__':
    main()
