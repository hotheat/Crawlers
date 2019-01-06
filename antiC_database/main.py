from lxml import html
from utils import log
import url_page
import os
import threading


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


def multi_thread(url, file):
    # MultiThreads
    log('Multi threading starts.')
    threads = []
    n = 14
    for i in range(n):
        url_n = get_url(url, i)
        t = MyThread(get_result, (url_n, file), get_result.__name__)
        threads.append(t)
        i += 1
    for i in range(n):
        threads[i].start()
    # join 等待所有进程结束
    for i in range(n):
        threads[i].join()
    log('Multi threading ends.')


def single_thread(url, file):
    # Single Thread
    log('Single threading starts.')
    for i in range(14):
        if i != 0:
            query = '='.join(('page', str(i)))
            url_n = '?'.join((url, query))
        else:
            url_n = url
        log('url', url_n)
        get_result(url_n, file)
    log('Single threading starts.')


def main():
    url = 'http://aps.unmc.edu/AP/database/antiC.php'
    mt_file = 'Antimicrobial_Peptide_m_t.fasta'
    st_file = 'Antimicrobial_Peptide_s_t.fasta'
    delelte(st_file, mt_file)
    # single_thread(url, st_file)
    multi_thread(url, mt_file)


if __name__ == '__main__':
    main()
