import sys
import tqdm
import requests
import time
import argparse
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


def load_local_html(file_path: str) -> str:
    """
    从本地文件加载HTML内容

    Args:
        file_path: HTML文件路径

    Returns:
        HTML内容字符串
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='豆瓣小组帖子爬虫')
    parser.add_argument('--mode', choices=['local', 'remote'], default='remote',
                       help='爬取模式：local-本地HTML文件，remote-远程网站（默认）')
    parser.add_argument('--file', type=str, default='response.html',
                       help='本地模式下的HTML文件路径（默认：response.html）')
    parser.add_argument('--group-id', type=str, default='724338',
                       help='远程模式下的小组ID（默认：724338）')
    parser.add_argument('--page', type=int, default=0,
                       help='远程模式下的页码（默认：0）')

    args = parser.parse_args()

    # 创建输出目录（输出到项目根目录的data文件夹）
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    if args.mode == 'local':
        # 本地模式：读取本地HTML文件
        print(f"本地模式：正在读取 {args.file}\n")

        # 支持相对路径和绝对路径
        html_file = Path(args.file)
        if not html_file.is_absolute():
            # 如果是相对路径，从项目根目录查找
            html_file = Path(__file__).parent.parent / args.file

        if not html_file.exists():
            print(f"错误：文件 {html_file} 不存在")
            sys.exit(1)

        try:
            # 读取本地HTML文件
            html_content = load_local_html(str(html_file))

            # 创建解析器并解析
            douban_parser = DoubanPostParser(html_content)
            data = douban_parser.parse()

            # 保存为JSON
            output_file = output_dir / f"local_{data['post']['post_id']}.json"
            douban_parser.save_json(str(output_file))

            print(f"\n完成！数据已保存到 {output_file}")

        except Exception as e:
            print(f"\n处理本地HTML文件时出错: {e}")
            sys.exit(1)

    else:
        # 远程模式：从网站爬取
        print(f"远程模式：正在爬取小组 {args.group_id} 第 {args.page} 页\n")

        # 获取帖子列表
        posts = get_post_list(group_id=args.group_id, page=args.page)

        print(f"获取到 {len(posts)} 个帖子，开始下载和解析...\n")

        # 遍历每个帖子
        for idx, post in enumerate(tqdm.tqdm(posts, desc="处理帖子")):
            try:
                # 下载网页HTML
                html_content = download_html(post["url"])

                # 创建解析器并解析
                douban_parser = DoubanPostParser(html_content)
                data = douban_parser.parse()

                # 保存为JSON
                output_file = output_dir / f"{idx}_{data['post']['post_id']}.json"
                douban_parser.save_json(str(output_file))

                # 添加延迟，避免请求过快
                time.sleep(1)

            except Exception as e:
                print(f"\n处理第 {idx+1} 个帖子时出错: {e}")
                print(f"帖子URL: {post['url']}")
                continue

        print(f"\n完成！共处理 {len(posts)} 个帖子")
