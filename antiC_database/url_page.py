import ssl
import socket
from utils import log
import gzip


def parsed_url(url):
    # 检查协议
    protocol = 'http'
    if url[:7] == 'http://':
        u = url.split('://')[1]
    elif url[:8] == 'https://':
        protocol = 'https'
        u = url.split('://')[1]
    else:
        # '://' 定位 然后取第一个 / 的位置来切片
        u = url

    # 检查默认 path
    i = u.find('/')
    if i == -1:
        host = u
        path = '/'
    else:
        host = u[:i]
        path = u[i:]

    # 检查端口
    port_dict = {
        'http': 80,
        'https': 443,
    }
    # 默认端口
    port = port_dict[protocol]
    if host.find(':') != -1:
        h = host.split(':')
        host = h[0]
        port = int(h[1])
    return protocol, host, port, path


def socket_by_protocol(protocol):
    """
    根据协议返回一个 socket 实例
    """
    if protocol == 'http':
        s = socket.socket()
    else:
        # HTTPS 协议需要使用 ssl.wrap_socket 包装一下原始的 socket
        # 除此之外无其他差别
        s = ssl.wrap_socket(socket.socket())
    return s


def response_by_socket(s):
    """
    参数是一个 socket 实例
    返回这个 socket 读取的所有数据
    """
    response = b''
    buffer_size = 1024
    while True:
        r = s.recv(buffer_size)
        if len(r) == 0:
            break
        response += r
    return response


def parsed_response(r):
    """
    把 response 解析出 状态码 headers body 返回
    状态码是 int
    headers 是 dict
    body 是 str
    """
    header, body = r.split('\r\n\r\n', 1)
    h = header.split('\r\n')
    status_code = h[0].split()[1]
    status_code = int(status_code)

    headers = {}
    for line in h[1:]:
        k, v = line.split(': ', 1)
        headers[k] = v
    return status_code, headers, body


# 复杂的逻辑全部封装成函数
def get(url):
    """
    用 GET 请求 url 并返回响应
    """
    protocol, host, port, path = parsed_url(url)
    s = socket_by_protocol(protocol)
    s.connect((host, port))
    # # cookie 实际上服务器用来识别身份的工具，判断是否登录
    request = 'GET {} HTTP/1.1\r\n' \
              'host: {}\r\n' \
              'User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
              'Chrome/62.0.3202.75 Safari/537.36\r\n' \
              'Connection: close\r\n' \
              'X-UDID:AEBCsYTjlQyPTjltS51ugZJy7bNvgrhtQBc=\r\n' \
              'Cookie: q_c1=0acfe69a89b5408280edc08edbbd6ab2|1508997291000|1508997291000; r_cap_id="MDdhNTg3ZmUxMTNiNGE3Mjk0NzE0NTI2YjA2ZjUzODY=|1508997291|4e88310e71e4dbb64011af4902d191cfa9421549"; cap_id="Y2FjMWUyMGRhNmU4NGFlOGJkMWZkYThjODhkMTFjN2U=|1508997291|d13222d93e27c09c903eacb1d7d0d07f9a7a2adf"; d_c0="AEBCsYTjlQyPTjltS51ugZJy7bNvgrhtQBc=|1508997293"; _zap=1635fb41-dd0d-495c-a437-b53bf8718d77; z_c0=Mi4xeE9BREFBQUFBQUFBUUVLeGhPT1ZEQmNBQUFCaEFsVk4wTWJlV2dBYWNoY2dnNUhlMHN3MldHazM0TmsxeVNCdHhn|1508997328|69964b73d8df1202a274c44454429cb09b343408; aliyungf_tc=AQAAAMIanyUVZAYAbOxQ3/Qb+RJetQo6; _xsrf=c53022fa-a3a0-4524-baf0-f9d0f696113c\r\n\r\n' \
        .format(path, host)
    encoding = 'utf-8'
    s.send(request.encode(encoding))
    response = response_by_socket(s)
    try:
        r = response.decode(encoding)
    except UnicodeDecodeError:
        encoding = 'ISO-8859-1'
        r = response.decode(encoding)
    status_code, headers, body = parsed_response(r)
    if status_code == 301:
        url = headers['Location']
        return get(url)
    return status_code, headers, body
