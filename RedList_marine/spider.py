import os
from pyquery import PyQuery as pq
from selenium import webdriver
import time
import re
import json
import random

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

# 打开带配置信息的phantomJS浏览器
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


class SpeciesInfo(Model):
    def __init__(self):
        self.sci_name = ''
        self.common_name = ''
        self.status = ''
        self.trend = ''


def specie_from_li(li):
    e = pq(li)
    spin = SpeciesInfo()
    desc = e.text().strip()
    spin.sci_name = e('.sciname').text().strip()
    for i, v in enumerate(desc.split('\n')):
        if i == 0 and re.search(r'\((.*)\)', v):
            spin.common_name = re.search(r'\((.*)\)', v).group(1)
        if re.match(r'Status', v):
            spin.status = re.split(r':|ver', v)[1].strip()
        if re.match(r'Pop\. trend:', v):
            spin.trend = re.split(':', v)[1].strip()
    return spin


def species_from_lis(url, i):
    c = cached_url(url, 'parsed_html', 'id-{}.html'.format(i))
    e = pq(c)
    lis = e('#results li .desc')
    species = [specie_from_li(li) for li in lis]
    return species


def cached_url(url, dir_name, filename):
    """
    缓存, 避免重复下载网页浪费时间
    """
    folder = dir_name
    path = os.path.join(folder, filename)
    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    if os.path.exists(path):
        print('已经存在{}'.format(url), flush=True)
        with open(path, 'rb') as f:
            s = f.read()
            return s
    else:
        # 建立 cached 文件夹
        if not os.path.exists(folder):
            os.makedirs(folder)
        print('正在爬取{}'.format(url), flush=True)
        driver.get(url)
        with open(path, 'wb') as f:
            f.write(driver.page_source.encode())
        content = driver.page_source
        return content


def save(species, path, filename):
    if not os.path.exists(path):
        os.mkdir(path)
    path = os.path.join(path, filename)
    ss = [sp.__dict__ for sp in species]
    dump = json.dumps(ss, indent=2, ensure_ascii=False)
    with open(path, 'w+', encoding='utf-8') as f:
        f.write(dump)


def get_result():
    result = []
    json_ix = 1
    for i in range(1, 1873):
        url = f'http://www.iucnredlist.org/search?page={i}'
        sps = species_from_lis(url, i)
        result.extend(sps)
        if i % 500 == 0:
            save(result, 'result', f'marine_red_list_{json_ix}.json')
            result = []
            json_ix += 1
            print(json_ix)
    save(result, 'result', f'marine_red_list_{json_ix}.json')


def run_time(s, e):
    m, s = divmod(e - s, 60)
    h, m = divmod(m, 60)
    print("运行时间：%02d:%02d:%02d" % (h, m, s))


def single_url_test():
    get_result()


def main():
    s = time.time()
    print('starts at {}.'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())), flush=True)
    get_result()
    e = time.time()
    run_time(s, e)
    print('END')
    print('ends at {}.'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())), flush=True)


if __name__ == '__main__':
    main()
