import time
import os

def log(*args, **kwargs):
    """
    用这个 log 替代 print
    time.time() 返回 unix time
    如何把 unix time 转化为人类能看得懂的格式
    """
    format = '%Y/%m/%d %H:%M:%S'
    value = time.localtime(int(time.time()))
    dt = time.strftime(format, value)
    print(dt, *args, **kwargs)

def load_file(filename):
    with open(filename, encoding='utf-8') as f:
        return f.read()


def delete(*file):
    for i in file:
        if os.path.isfile(i):
            os.remove(i)