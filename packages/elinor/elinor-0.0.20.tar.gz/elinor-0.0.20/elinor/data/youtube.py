import requests
import re
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor
from deprecated import deprecated

def get_video_id_from_url(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# deprecated: 放弃纯正则匹配, 容易受到转义字符干扰, 改为使用 json 解析更加准确
# 改良版在get_youtube_title_by_url
@deprecated(reason="Use get_youtube_title_by_url instead")
def _get_youtube_title_by_url(url):
    import regex  # 第三方库，性能更强
    TITLE_PATTERN = regex.compile(r'"playerOverlayVideoDetailsRenderer":\{"title":\{"simpleText":"(.*?)"')
    try:
        response = requests.get(url, timeout=(30, 60))  # 设置连接和读取超时
        match = TITLE_PATTERN.search(response.text)  # 直接使用编译后的对象
        return match.group(1) if match else None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def get_youtube_title_by_url(url):
    try:
        response = requests.get(url, timeout=(30, 60))  # 设置连接和读取超时
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all("script", {'nonce': True})
        for script in scripts:
            if 'playerOverlayVideoDetailsRenderer' in script.text:
                json_str = script.string.strip()
                json_data = json.loads(json_str[json_str.find('{'):json_str.rfind('}')+1])
                title = json_data["playerOverlays"]\
                    ["playerOverlayRenderer"]\
                    ["videoDetails"]\
                    ["playerOverlayVideoDetailsRenderer"]\
                    ["title"]["simpleText"]
                return title
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def get_youtube_title_by_url_batch(urls, max_workers=None):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(get_youtube_title_by_url, urls))


def get_youtube_author_by_url(url):
    try:
        response = requests.get(url, timeout=(30, 60))  # 设置连接和读取超时
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all("script", {'nonce': True})

        for script in scripts:
            if 'playerOverlayVideoDetailsRenderer' in script.text:
                json_str = script.string.strip()
                json_data = json.loads(json_str[json_str.find('{'):json_str.rfind('}')+1])
                author = json_data["playerOverlays"]\
                    ["playerOverlayRenderer"]\
                    ["videoDetails"]\
                    ["playerOverlayVideoDetailsRenderer"]\
                    ["subtitle"]["runs"][0]["text"]
                return author
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def get_youtube_author_by_url_batch(urls, max_workers=None):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(get_youtube_author_by_url, urls))

def get_youtube_title_by_oembed(id_or_url):
    api_prefix = "https://www.youtube.com/oembed?url="
    try:
        if "youtube.com/watch?v=" in id_or_url:
            video_id = get_video_id_from_url(id_or_url)
            url = api_prefix + f"https://www.youtube.com/watch?v={video_id}&format=json"
        elif len(id_or_url) == 11:
            url = api_prefix + f"https://www.youtube.com/watch?v={id_or_url}&format=json"
        else:
            raise ValueError("Invalid YouTube ID or URL format")
        response = requests.get(url, timeout=(30, 60))  # 设置连接和读取超时
        data = response.json()
        return data.get("title")
    except Exception as e:
        print(f"Error fetching oEmbed for {url}: {e}")
        return None
    

def get_youtube_title_by_oembed_batch(ids_or_urls, max_workers=None):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(get_youtube_title_by_oembed, ids_or_urls))


def get_youtube_info_by_oembed(id_or_url):
    api_prefix = "https://www.youtube.com/oembed?url="
    try:
        if "youtube.com/watch?v=" in id_or_url:
            video_id = get_video_id_from_url(id_or_url)
            url = api_prefix + f"https://www.youtube.com/watch?v={video_id}&format=json"
        elif len(id_or_url) == 11:
            url = api_prefix + f"https://www.youtube.com/watch?v={id_or_url}&format=json"
        else:
            raise ValueError("Invalid YouTube ID or URL format")
        response = requests.get(url, timeout=(30, 60))  # 设置连接和读取超时
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching oEmbed for {url}: {e}")
        return None
    
def get_youtube_info_by_oembed_batch(ids_or_urls, max_workers=None):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(get_youtube_info_by_oembed, ids_or_urls))