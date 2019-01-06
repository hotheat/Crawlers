from lxml import html
from utils import log
import url_page
import os
import threading
import queue


class DownloadThread(threading.Thread):
    def __init__(self, queue, file):
        threading.Thread.__init__(self)
        self.queue = queue
        self.file = file

    def run(self):
        while True:
            # 从队列中取元素
            url = self.queue.get()
            self.download_file(url)
            self.queue.task_done()

    def download_file(self, url):
        get_result(url, self.file)


class Model(object):
    def __str__(self):
        class_name = self.__class__.__name__
        properties = (u'{} = {}'.format(k, v) for k, v in self.__dict__.items())
        r = u'\n<{}:\n {}\n>'.format(class_name, u'\n  '.join(properties))
        return r


class Peptide(Model):
    def __init__(self):
        self.id = ''
        self.sequence = ''


def join_url(url, href):
    protocol, host, _, path = url_page.parsed_url(url)
    path = path.rsplit('/', 1)[0] + '/'
    href = ''.join(href)
    pep_url = ''.join((host, path, href))
    return pep_url


def peps_from_href(table):
    pep = Peptide()
    trs = table.xpath('.//tr')
    pep_id = trs[0].xpath('td')[2].xpath('.//p')[0].text
    pep.id = pep_id
    pep_seq = trs[3].xpath('td')[2].xpath('.//p/font')[0].text
    pep.sequence = pep_seq
    return pep


def href_from_bs(b, url):
    hf = b.xpath('./a/@href')
    url = join_url(url, hf)
    _, _, page = url_page.get(url)
    root = html.fromstring(page)
    table = root.xpath('//table')[2]
    pep = peps_from_href(table)
    return pep


def peps_from_url(url):
    _, _, page = url_page.get(url)
    root = html.fromstring(page)
    bs = root.xpath('//b')[1:]
    e = 'Program ends.'
    assert bs != [], e
    peps = [href_from_bs(b, url) for b in bs]
    return peps


def generate_fasta(file, pep):
    with open(file, 'a') as w:
        for p in pep:
            s = '\n'.join((('>' + p.id), (p.sequence + '\n')))
            w.write(s)


def delelte(*file):
    for i in file:
        if os.path.isfile(i):
            os.remove(i)


def get_result(url_n, file):
    peps = []
    pep = peps_from_url(url_n)
    peps.append(pep)
    generate_fasta(file, pep)


def get_url(url, n):
    if n != 0:
        query = '='.join(('page', str(n)))
        url_n = '?'.join((url, query))
    else:
        url_n = url
    log('url_n', url_n)
    return url_n


def main():
    url = 'http://aps.unmc.edu/AP/database/antiC.php'
    mt_file = 'Antimicrobial_Peptide_m_t_queue.fasta'
    q = queue.Queue()

    # log('Multi threading starts.')
    # # 创建线程池, 设定线程数量
    # for i in range(14):
    #     t = DownloadThread(q, mt_file)
    #     t.setDaemon(True)
    #     t.start()
    #
    # # 往队列中添加元素
    # for i in range(14):
    #     url_n = get_url(url, i)
    #     q.put(url_n)
    # q.join()
    # log('Multi threading starts.')

    ######## 测试阻塞 ##########

    # 创建线程池, 设定线程数量
    #### 先爬 1 个, 再同时爬 9 个, 爬完剩下的######
    rs = [
        range(0, 1),
        range(1, 10),
        range(10, 14),
    ]

    def spider(r, q, mt_file, url):
        log('Multi threading starts.')
        for i in r:
            t = DownloadThread(q, mt_file)
            t.setDaemon(True)
            t.start()
        # 往队列中添加元素
        for i in r:
            url_n = get_url(url, i)
            q.put(url_n)
        # join() 阻塞
        q.join()
        log('Multi threading ends.')

    for r in rs:
        spider(r, q, mt_file, url)


if __name__ == '__main__':
    main()
