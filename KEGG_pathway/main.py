from utils import log, load_file, delete
from lxml import etree
import re
import requests


class Model(object):
    def __str__(self):
        class_name = self.__class__.__name__
        properties = (u'{} = {}'.format(k, v) for k, v in self.__dict__.items())
        r = u'\n<{}:\n {}\n>'.format(class_name, u'\n  '.join(properties))
        return r


class KeggPath(Model):
    def __init__(self):
        self.id = ''
        self.name = ''
        self.title = ''
        self.subtitle = ''


def kegg_from_list(kegg_ls):
    dls = kegg_ls.xpath('.//dl')
    dts = dls[0].xpath('.//dt')
    dds = dls[0].xpath('.//dd')
    keggs = []
    for i in range(len(dts)):
        kegg = KeggPath()
        kegg.id = dts[i].text
        kegg.name = dds[i].xpath('.//a')[0].text
        keggs.append(kegg)
    return keggs


def keggs_from_url(url):
    html_content = requests.get(url).content
    # html_content = load_file(url)
    page = etree.HTML(html_content)
    ts = page.xpath('//h4')
    subts = page.xpath('//b')
    titles = [ts[i].text for i in range(2, len(ts) - 1)]
    r_sub = re.compile(r'\d+\.\d+[\s.]+')
    subtitles = [subts[i].text for i in range(len(subts)) if r_sub.match(subts[i].text)]
    lists = page.xpath('//div[@class="list"]')[1:]
    keggs = [kegg_from_list(i) for i in lists]
    return titles, subtitles, keggs


def combine(titles, subtitles, keggs):
    id_title = {i.split('.')[0]: i.split(' ', 1)[1]
                for i in titles}
    tit_subs = []
    for i in subtitles:
        n = i.split('.')[0]
        t_sub = (id_title[n], i.split(' ', 1)[1])
        tit_subs.append(t_sub)
    for i, v in enumerate(keggs):
        for j in v:
            j.title = tit_subs[i][0]
            j.subtitle = tit_subs[i][1]
    return keggs


def generate_fasta(file, keggs):
    with open(file, 'w', encoding='utf-8') as w:
        w.write('\t'.join(('id', 'name', 'title', 'subtitle')) + '\n')
        for i in keggs:
            for j in i:
                s = '\t'.join(('ko'+j.id, j.name, j.title, j.subtitle)) + '\n'
                w.write(s)


def get_result(url, file):
    titles, subtitles, keggs = keggs_from_url(url)
    keggs = combine(titles, subtitles, keggs)
    generate_fasta(file, keggs)


def single_thread(url, file):
    # Single Thread
    log('Single threading starts.')
    get_result(url, file)
    log('Single threading ends.')


def main():
    url = 'https://www.genome.jp/kegg/pathway.html'
    path_file = './KEGG.pathway.tab'
    single_thread(url, path_file)


if __name__ == '__main__':
    main()
