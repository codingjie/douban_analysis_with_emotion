import requests
from lxml import etree
from typing import List, Dict, Optional


def get_post_list(group_id: str, page: int = 0, headers: Optional[Dict] = None, cookies: Optional[Dict] = None) -> List[Dict[str, str]]:
    """
    获取豆瓣小组的帖子列表
    
    Args:
        group_id: 小组ID（例如：724338）
        page: 页码，从0开始
        headers: 请求头，如果为None则使用默认请求头
        cookies: Cookie，如果为None则使用默认Cookie
    
    Returns:
        帖子列表，每个帖子包含title和url字段
        [
            {
                "title": "帖子标题",
                "url": "帖子链接"
            },
            ...
        ]
    """
    # 默认请求头
    default_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": f"https://www.douban.com/group/{group_id}/discussion?start={page*25}&type=new",
        "sec-ch-ua": "\"Microsoft Edge\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
    }
    
    # 默认Cookie
    default_cookies = {
        "bid": "rvRVLPPPKT0",
        "ll": "118282",
        "_pk_id.100001.8cb4": "de1ad5d2bb573d2c.1767493104.",
        "__utma": "30149280.943706779.1767493104.1767493104.1767493104.1",
        "__utmc": "30149280",
        "__utmz": "30149280.1767493104.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)",
        "dbcl2": '"293011074:+je71xPd5og"',  # 登录凭证，重要！
        "ck": "ADje",  # 安全验证，重要！
        "push_noty_num": "0",
        "push_doumail_num": "0",
        "__utmv": "30149280.29301",
        "frodotk_db": "2a7d888a4cd6565a7f78999ee683030e",
        "__yadk_uid": "KIF2YtJSlfKuJqJdRb8e8TGr7BSy2Gbu",
        "_pk_ses.100001.8cb4": "1"
    }
    
    # 使用传入的headers和cookies，如果没有则使用默认值
    if headers is None:
        headers = default_headers
    else:
        headers = {**default_headers, **headers}
    
    if cookies is None:
        cookies = default_cookies
    else:
        cookies = {**default_cookies, **cookies}
    
    # 构建URL和参数
    url = f"https://www.douban.com/group/{group_id}/discussion"
    params = {
        "start": str(page * 25),
        "type": "new"
    }
    
    # 发送请求
    response = requests.get(url, headers=headers, cookies=cookies, params=params)
    response.raise_for_status()
    
    # 解析HTML
    html = etree.HTML(response.text)
    
    # 使用xpath表达式提取帖子列表
    # //td[@class='title']/a[@href]
    post_links = html.xpath("//td[@class='title']/a[@href]")
    
    # 提取帖子信息
    post_list = []
    for link in post_links:
        title = link.text.strip() if link.text else ""
        url = link.get('href', '')
        
        # 补全URL（如果是相对路径）
        if url and not url.startswith('http'):
            url = 'https://www.douban.com' + url
        
        if title and url:
            post_list.append({
                "title": title,
                "url": url
            })
    
    return post_list


if __name__ == "__main__":
    # 示例用法
    import sys
    import io
    
    # 设置输出编码为UTF-8（解决Windows控制台编码问题）
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    group_id = "724338"
    page = 0
    
    posts = get_post_list(group_id, page)
    
    print(f"获取到 {len(posts)} 个帖子：\n")
    for idx, post in enumerate(posts, 1):
        print(f"{idx}. {post['title']}")
        print(f"   URL: {post['url']}\n")