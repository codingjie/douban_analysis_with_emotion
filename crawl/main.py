import sys
import tqdm
import requests
import time
from pathlib import Path

sys.path.append("..")

from get_list import get_post_list
from parser import DoubanPostParser


def download_html(url: str, headers: dict = None, cookies: dict = None) -> str:
    """
    下载网页HTML内容
    
    Args:
        url: 网页URL
        headers: 请求头
        cookies: Cookie
    
    Returns:
        HTML内容字符串
    """
    default_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0"
    }
    
    default_cookies = {
        "bid": "Sx-OD3y3uFs",
        "_pk_id.100001.8cb4": "54b1b2cc6d6373b3.1738384552.",
        "__yadk_uid": "deF7TCDjFs6zwrhiCa2iCnwvGXPjJWeE",
    }
    
    if headers is None:
        headers = default_headers
    else:
        headers = {**default_headers, **headers}
    
    if cookies is None:
        cookies = default_cookies
    else:
        cookies = {**default_cookies, **cookies}
    
    response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
    response.raise_for_status()
    response.encoding = 'utf-8'
    return response.text


if __name__ == "__main__":
    # 创建输出目录（输出到项目根目录的data文件夹）
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    # 获取帖子列表
    group_id = "724338" # 跨年龄段烦恼交流会
    page = 0
    posts = get_post_list(group_id=group_id, page=page)
    
    print(f"获取到 {len(posts)} 个帖子，开始下载和解析...\n")
    
    # 遍历每个帖子
    for idx, post in enumerate(tqdm.tqdm(posts, desc="处理帖子")):
        try:
            # 下载网页HTML
            html_content = download_html(post["url"])
            
            # 创建解析器并解析
            parser = DoubanPostParser(html_content)
            data = parser.parse()
            
            # 保存为JSON
            output_file = output_dir / f"{idx}_{data['post']['post_id']}.json"
            parser.save_json(str(output_file))
            
            # 添加延迟，避免请求过快
            time.sleep(1)
            
        except Exception as e:
            print(f"\n处理第 {idx+1} 个帖子时出错: {e}")
            print(f"帖子URL: {post['url']}")
            continue
    
    print(f"\n完成！共处理 {len(posts)} 个帖子")