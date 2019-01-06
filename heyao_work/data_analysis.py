import sys
import pandas as pd
from lxml import etree
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib
import argparse
import time

matplotlib.style.use('ggplot')


def load_file(filename):
    with open(filename, encoding='utf-8') as f:
        return f.read()


class Sale_data(object):
    def __init__(self):
        self.date = ''
        self.sales = 0
        self.qty = 0
        self.customer = 0


def join_str(str_item):
    return ''.join([i.strip() for i in str_item])


def sale_from_tr(tr):
    s = Sale_data()
    tds = tr.xpath('.//td')
    sales = [join_str(tds[i].xpath('./text()'))
             for i in [0, 1, 3, 8]]
    s.date, s.sales, s.qty, s.customer = \
        sales[0], sales[1], sales[2], sales[3]
    return s


def data_to_df(datas):
    sales_data = {}
    for i in datas:
        for k, v in i.__dict__.items():
            sales_data.setdefault(k, [])
            sales_data[k].append(v)
    df = pd.DataFrame(sales_data)
    return df


def parse_html(html):
    html_content = load_file(html)
    page = etree.HTML(html_content)
    datas = []
    flag = ['even', 'odd']
    for i in flag:
        table = page.xpath('//tr[@class="{}"]'.format(i))
        data = [sale_from_tr(k) for k in table]
        datas.extend(data)
    df = data_to_df(datas)
    return df


class Analysis_data(object):
    def __init__(self):
        self.fig, self.axs = plt.subplots(3, 1, sharex=True, figsize=(16, 12))
        self.time = time.strftime("%H-%M-%S", time.localtime())

    def _to_date_df(self, data):
        df = pd.DataFrame(data)
        df['date'] = pd.DatetimeIndex(df['date'])
        df.sort_values('date', inplace=True)
        df.set_index('date', drop=True, inplace=True)
        df = df.astype('int64')
        return df

    def combine_df(self, name, *df):
        if name == 'customer':
            to_df = pd.DataFrame({
                'total': df[0]['sales'] / df[0][name],
                'running': df[1]['sales'] / df[1][name],
                'walking': df[2]['sales'] / df[2][name],
            })
        elif name == 'qty':
            to_df = pd.DataFrame({
                'total': df[0][name] / df[0]['customer'],
                'running': df[1][name] / df[1]['customer'],
                'walking': df[2][name] / df[2]['customer'],
            })
        else:
            to_df = pd.DataFrame({
                'total': df[0][name],
                'running': df[1][name],
                'walking': df[2][name],
            })
        return to_df

    def _configure_xaxis(self, _ax):
        # 将 x 轴设为日期时间格式
        _ax.xaxis_date()
        rule = mdates.rrulewrapper(mdates.DAILY, interval=1)
        loc = mdates.RRuleLocator(rule)
        formatter = mdates.DateFormatter('%d %b')
        _ax.xaxis.set_major_locator(loc)
        _ax.xaxis.set_major_formatter(formatter)
        xlabels = _ax.get_xticklabels()
        plt.setp(xlabels, rotation=30, fontsize=9)
        # 日期的排列根据图像的大小自适应
        self.fig.autofmt_xdate()

    def visualization(self, df, n, sale_axs):
        ax = sale_axs[n][0]
        for i in df.columns:
            ax.plot(df[i].index, df[i].values, lw=3.5, marker='o')
            ax.set_title(sale_axs[n][1])
        self._configure_xaxis(ax)

    def group_week(self, *df):
        n = 1
        group = []
        for i in range(1, len(df[0]) + 1):
            if i % 7 != 0:
                group.append(n)
            else:
                group.append(n)
                n += 1
        tmp = []
        for i in df:
            i['week'] = group
            i = i.groupby('week').sum()
            print(i.head())
            i['price_per_customer'] = i['sales'] / i['customer']
            i['quantity_per_customer'] = i['qty'] / i['customer']
            tmp.append(i)
        return tmp

    def week_to_csv(self, *df):
        df_groups = self.group_week(*df)
        df_group = pd.concat([df_groups[0], df_groups[1], df_groups[2]],
                             keys=['walk', 'running', 'total'])
        df_group.to_csv('group_week.csv')

    def deal_data(self, walk_html, run_html):
        walk = parse_html(walk_html)
        run = parse_html(run_html)
        walk_df, run_df = self._to_date_df(walk), self._to_date_df(run)
        tot_df = walk_df + run_df
        self.week_to_csv(walk_df, run_df, tot_df)
        sale_axs = {'sales': [self.axs[0], 'TO'],
                    'qty': [self.axs[1], 'Quantity per customer'],
                    'customer': [self.axs[2], 'Price per customer'], }
        for i in sale_axs:
            sale_df = self.combine_df(i, tot_df, run_df, walk_df)
            self.visualization(sale_df, i, sale_axs)
        self.axs[0].legend(['total', 'walking', 'running'], loc='best')
        plt.tight_layout()
        df_len = len(tot_df)
        xlim = plt.xlim()[1] - plt.xlim()[0]
        plt.xlim([plt.xlim()[0] - xlim / df_len, plt.xlim()[1] + xlim / df_len])
        plt.savefig('./{}-stat-day.png'.format(self.time))


def get_arg():
    parse = argparse.ArgumentParser(
        description="""status of decathlon web data.""")
    parse.add_argument("walk_html", metavar="walk_html", help="walk.html")
    parse.add_argument("run_html", metavar="run_html", help="running.html")
    arg = parse.parse_args().__dict__
    return arg


def main():
    arg = get_arg()
    s = Analysis_data()
    s.deal_data(**arg)


if __name__ == '__main__':
    main()
