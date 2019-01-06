"""
爬取 Scarlett Johansson 的相册和电影海报
1. 分别用 selenium webdriver 中的 chrome 和 phantomjs 模拟网页加载
2. 加入已加载网页的本地缓存
3. 数据存储采用 json 本地存储
4. 采用 xpath helper 帮助解析
"""

import os
from selenium import webdriver
from lxml import html
import json
import requests
import random


def chrome_driver():
    # 设置 chrome 不弹窗
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    return driver


def phantomjs():
    driver = webdriver.PhantomJS()
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
    # dcap["phantomjs.page.settings.loadImages"] = False
    driver.set_window_size(800, 600)
    # 设置代理
    service_args = ['--ignore-ssl-errors=true', '--ssl-protocol=TLSv1']
    # 打开带配置信息的 phantomJS 浏览器
    driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=service_args)
    # 隐式等待5秒，可以自己调节
    driver.implicitly_wait(10)
    # 设置10秒页面超时返回，类似于requests.get()的timeout选项，driver.get()没有timeout选项
    # 以前遇到过driver.get(url)一直不返回，但也不报错的问题，这时程序会卡住，设置超时选项能解决这个问题。
    driver.set_page_load_timeout(10)
    # 设置10秒脚本超时时间
    driver.set_script_timeout(10)
    return driver


def make_dir(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


class Model(object):
    """
    基类, 用来显示类的信息
    """

    def __repr__(self):
        name = self.__class__.__name__
        properties = ('{}=({})'.format(k, v) for k, v in self.__dict__.items())
        s = '\n<{} \n  {}>'.format(name, '\n  '.join(properties))
        return s


class Poster(Model):
    def __init__(self):
        self.title = ''
        self.src = ''


def poster_from_url(title, src):
    p = Poster()
    p.title = title
    p.src = src
    return p


def cached_url(folder, filename, url, driver):
    """
    缓存, 避免重复下载网页浪费时间
    """
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            s = f.read()
            return s
    else:
        # 建立 cached 文件夹
        make_dir(folder)
        driver.get(url)
        # 发送网络请求, 把结果写入到文件夹中
        with open(path, 'wb') as f:
            f.write(driver.page_source.encode())
        content = driver.page_source
        return content


def save_json(posters, filename):
    ps = [p.__dict__ for p in posters]
    dump = json.dumps(ps, indent=2, ensure_ascii=False)
    with open(filename, 'w+', encoding='utf-8') as f:
        f.write(dump)


def save_data(posters):
    for i, p in enumerate(posters):
        download_image('poster', str(i), p.src)
    save_json(posters, 'poster.json')


def download_image(folder, filename, url):
    path = os.path.join(folder, filename) + '.png'
    if os.path.exists(path):
        return

    make_dir(folder)
    headers = {
        'user-agent': '''Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.98 Safari/537.36
        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8''',
    }
    r = requests.get(url, headers)
    with open(path, 'wb') as f:
        f.write(r.content)


def download_pic(urlstart, total, step=20):
    driver = chrome_driver()
    for i in range(0, total, step):
        url = urlstart.format(str(i))
        folder = 'cached/html'
        filename = url.rsplit('=', 1)[-1] + '.html'
        page = cached_url(folder, filename, url, driver)
        pre = html.fromstring(page).xpath('//pre')[0].text
        response = json.loads(pre)
        for image in response['images']:
            im_url, id = image['src'], image['id']
            print('im', im_url, id)
            download_image('img', id, im_url)


def download_poster(url):
    # 用 headless chrome 拿不到 html 页面
    driver = phantomjs()
    page = cached_url('cached/poster', 'Scarlett Johansson.html', url, driver)
    src_path = "//div[@class='item-root']/a[@class='cover-link']/img[@class='cover']/@src"
    root = html.fromstring(page)
    srcs = root.xpath(src_path)
    title_path = "//div[@class='item-root']/div[@class='detail']/div[@class='title']/a[@class='title-text']"
    titlexpath = root.xpath(title_path)
    titles = [i.text for i in titlexpath]
    posters = [poster_from_url(t, s) for t, s in zip(titles, srcs)]
    save_data(posters)


if __name__ == '__main__':
    url = 'https://www.douban.com/j/search_photo?q=Scarlett%20Johansson&limit=20&start={}'
    total = 100
    download_pic(url, total)

    url = 'https://movie.douban.com/subject_search?search_text=Scarlett+Johansson&cat=1002'
    download_poster(url)
