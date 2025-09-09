import requests
from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
from typing import List
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 代理源 URL 列表 (使用可直接访问的免费代理列表)
PROXY_SOURCES = [
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=https",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all",
]

# 测试代理可用性的 URL
TEST_URL = "http://httpbin.org/ip"

# 本地保存有效代理的文件
PROXY_FILE = "proxies.json"

# 请求头部信息
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


# 代理池存储类
class ProxyStorage:
    def __init__(self):
        self.proxies = set()
        if os.path.exists(PROXY_FILE):
            try:
                with open(PROXY_FILE, "r", encoding="utf-8") as f:
                    self.proxies = set(json.load(f))
                logger.info(f"Loaded {len(self.proxies)} proxies from {PROXY_FILE}")
            except Exception as e:
                logger.error(f"Error loading proxies from file: {e}")
                self.proxies = set()

    def add(self, proxy: str):
        if proxy not in self.proxies:
            self.proxies.add(proxy)
            # 实时追加到文件中
            try:
                with open(PROXY_FILE, "r+", encoding="utf-8") as f:
                    try:
                        existing_proxies = json.load(f)
                    except:
                        existing_proxies = []

                    if proxy not in existing_proxies:
                        existing_proxies.append(proxy)
                        f.seek(0)
                        f.truncate()
                        json.dump(existing_proxies, f, ensure_ascii=False, indent=2)
            except FileNotFoundError:
                with open(PROXY_FILE, "w", encoding="utf-8") as f:
                    json.dump([proxy], f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error appending proxy to file: {e}")

    def remove(self, proxy: str):
        self.proxies.discard(proxy)

    def all(self):
        return list(self.proxies)

    def save(self):
        try:
            with open(PROXY_FILE, "w", encoding="utf-8") as f:
                json.dump(list(self.proxies), f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.proxies)} proxies to {PROXY_FILE}")
        except Exception as e:
            logger.error(f"Error saving proxies to file: {e}")


storage = ProxyStorage()


# 抓取代理列表
def fetch_proxies() -> List[str]:
    proxies = []
    for url in PROXY_SOURCES:
        try:
            logger.info(f"Fetching proxies from {url}")
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            # 解析代理列表
            parsed_proxies = parse_proxies(resp.text)
            proxies.extend(parsed_proxies)
            logger.info(f"Got {len(parsed_proxies)} proxies from {url}")
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
    return list(set(proxies))  # 去重


# 解析代理列表
def parse_proxies(page_content: str) -> List[str]:
    proxies = []
    # 匹配 IP:Port 格式的代理
    proxy_pattern = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{1,5}\b")
    matches = proxy_pattern.findall(page_content)

    for match in matches:
        # 简单验证IP地址格式
        ip, port = match.split(":")
        if all(0 <= int(x) <= 255 for x in ip.split(".")):
            proxies.append(f"http://{match}")
            proxies.append(f"https://{match}")

    return list(set(proxies))  # 去重


# 验证代理可用性
def check_proxy(proxy: str) -> bool:
    try:
        proxies_dict = {"http": proxy, "https": proxy}
        resp = requests.get(TEST_URL, proxies=proxies_dict, timeout=10, headers=HEADERS)
        if resp.status_code == 200:
            logger.info(f"✅ Valid proxy: {proxy}")
            storage.add(proxy)  # 已经在 ProxyStorage.add 中实现了实时追加到文件
            return True
    except requests.exceptions.Timeout:
        logger.warning(f"⏰ Timeout: {proxy}")
    except requests.exceptions.ConnectionError:
        logger.warning(f"🔌 Connection error: {proxy}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"❌ Request error: {proxy}, Error: {e}")
    except Exception as e:
        logger.warning(f"❌ Failed: {proxy}, Error: {e}")
    return False


# 验证所有代理的可用性
def validate_proxies(proxies: List[str]):
    logger.info(f"Validating {len(proxies)} proxies...")
    with ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(check_proxy, proxies))
    valid_count = sum(results)
    logger.info(f"Validation complete. {valid_count}/{len(proxies)} proxies are valid.")


# 主程序
if __name__ == "__main__":
    logger.info("🔄 Starting proxy fetching...")
    proxies = fetch_proxies()
    logger.info(f"✅ Fetching complete, got {len(proxies)} unique proxies")

    if proxies:
        logger.info("🔄 Starting proxy validation...")
        validate_proxies(proxies)
        storage.save()
        logger.info(f"💾 Saved {len(storage.all())} valid proxies to {PROXY_FILE}")
    else:
        logger.warning("⚠️ No proxies fetched")
