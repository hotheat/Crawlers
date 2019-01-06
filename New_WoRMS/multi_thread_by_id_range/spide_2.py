import os
from pyquery import PyQuery as pq
from selenium import webdriver
import json
import re
import threading
import numpy as np
import pandas as pd
import argparse
import time
import requests


def args_parse():
    parser = argparse.ArgumentParser(
        description='spider WoRMS',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-s", help="start id", default=0, type=int)
    parser.add_argument("-e", help="end id", required=True, type=int)
    parser.add_argument("-t", help="thread", default=10, type=int)
    args = parser.parse_args()
    return args


args = args_parse()
s, n, tn = args.s, args.e, args.t
err_log = open('err.log', 'a')


class MyThread(threading.Thread):
    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args

    def get_result(self):
        return self.res

    def run(self):
        self.res = self.func(*self.args)


class Model(object):
    """
    基类, 用来显示类的信息
    """

    def __repr__(self):
        name = self.__class__.__name__
        properties = ('{}=({})'.format(k, v) for k, v in list(self.__dict__.items()))
        s = '\n<{} \n  {}>'.format(name, '\n  '.join(properties))
        return s


class SpeciesInfo(Model):
    def __init__(self):
        self.aphiaID = ''
        self.classification = ''
        self.status = ''
        self.rank = ''
        self.parent = ''
        self.synonymised_name = ''
        self.child = ''
        self.environment = ''
        self.fossil_range = ''
        self.original_dscp = ''
        self.tax_citation = ''
        self.edit_date = ''
        self.edit_action = ''
        self.edit_by = ''


def save(species, path, filename):
    if not os.path.exists(path):
        os.mkdir(path)
    path = os.path.join(path, filename)
    ss = [sp.__dict__ for sp in species]
    dump = json.dumps(ss, indent=2, ensure_ascii=False)
    with open(path, 'w+', encoding='utf-8') as f:
        f.write(dump)


def cached_url(url, dir_name, filename, driver):
    """
    缓存, 避免重复下载网页浪费时间
    """
    folder = dir_name
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            s = f.read()
            return s
    else:
        # 建立 cached 文件夹
        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except FileExistsError:
            pass
        try:
            driver.get(url)
            content = driver.page_source
            if 'No results found' not in content:
                with open(path, 'wb') as f:
                    f.write(driver.page_source.encode())
        except Exception as e:
            err_log.write("Error" + url + '\t' + str(e) + '\n')
            with open('error/error.html', 'wb') as f:
                f.write(driver.page_source.encode())
            content = driver.page_source
        return content


def cached_path(id):
    cut = pd.cut(list(range(s, n + 1)), bins=10)
    cats = cut.categories[cut.codes]
    r = str(cats[id - s])
    r = re.sub('[\(|\]|\s]', '', r)
    r = r.replace(',', '-')
    return r


def parse(url, i, driver):
    path = cached_path(i)
    c = cached_url(url, os.path.join('parsed_html', path), 'id-{}.html'.format(i), driver)
    e = pq(c)
    spin = SpeciesInfo()
    spin.aphiaID = e('#AphiaID').text()
    cls = e('#Classification ol.aphia_core_breadcrumb-classification')
    spin.classification = cls('li').text().strip()
    spin.status = e('#Status div.leave_image_space').text().strip()
    spin.rank = e('#Rank div.leave_image_space').text().strip()
    spin.parent = e('#Parent div.leave_image_space').text().strip()
    spin.synonymised_name = e('#SynonymisedNames').text().strip()
    spin.child = e("#ChildTaxa").text().strip()
    spin.environment = e('#Environment').text()
    spin.fossil_range = e('#FossilRange').text()
    spin.original_dscp = e('#OriginalDescription').text()
    spin.tax_citation = e('#Citation').text()
    spin.edit_date = e('#TaxonomicEditHistory').find('div.col-xs-5').text()
    spin.edit_action = e('#TaxonomicEditHistory').find('div.col-xs-3').text()
    spin.edit_by = e('#TaxonomicEditHistory').find('div.col-xs-4 a').text()
    return spin


def get_result(ranges):
    driver = webdriver.PhantomJS()
    spins = []
    s = re.findall('\d+', str(ranges))
    file = '{}-{}.json'.format(s[0], s[1])
    for i, v in enumerate(ranges):
        url = 'http://www.marinespecies.org/aphia.php?p=taxdetails&id=' + str(v)
        if not parse(url, v, driver).aphiaID == "":
            spins.append(parse(url, v, driver))
    save(spins, 'json', file)


def run_time(s, e):
    m, s = divmod(e - s, 60)
    h, m = divmod(m, 60)
    print("运行时间：%02d:%02d:%02d" % (h, m, s), flush=True)


def multi_spider():
    start = time.time()
    print('Multi threading starts at {}.'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())), flush=True)
    threads = []
    splited_ranges = [range(i, i + int((n - s) / tn)) for i in range(s, n, int((n - s) / tn))]
    print(splited_ranges)
    for rs in splited_ranges:
        t = MyThread(get_result, (rs,), get_result.__name__)
        threads.append(t)
    for i in range(tn):
        threads[i].start()
    # join 等待所有进程结束
    for i in range(tn):
        threads[i].join()
    print('Multi threading ends at {}.'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())), flush=True)
    end = time.time()
    run_time(start, end)


def error_url():
    eu = 'http://www.marinespecies.org/aphia.php?p=taxdetails&id=0'
    e_dir = 'error'
    err_path = os.path.join(e_dir, 'error.html')
    if not os.path.exists(err_path):
        os.mkdir(e_dir)
    with open(err_path, 'wb') as w:
        c = requests.get(eu).content
        w.write(c)


def main():
    error_url()
    multi_spider()
    err_log.close()


if __name__ == '__main__':
    main()
