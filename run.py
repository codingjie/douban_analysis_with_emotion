"""
豆瓣帖子爬虫与情感分析系统 - 一键运行脚本
"""
import subprocess
import sys
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).parent.absolute()
CRAWL_DIR = ROOT_DIR / "crawl"
ANALYZE_DIR = ROOT_DIR / "analyze"
DATA_DIR = ROOT_DIR / "data"


def run_command(script_name, cwd, args=None):
    """运行Python脚本"""
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    subprocess.run(cmd, cwd=cwd)


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='豆瓣帖子爬虫与情感分析系统')
    parser.add_argument('--mode', choices=['local', 'remote'], default='remote',
                       help='爬取模式：local-本地HTML文件，remote-远程网站（默认）')
    parser.add_argument('--file', type=str, default='response.html',
                       help='本地模式下的HTML文件路径（默认：response.html）')
    parser.add_argument('--group-id', type=str, default='724338',
                       help='远程模式下的小组ID（默认：724338）')
    parser.add_argument('--page', type=int, default=0,
                       help='远程模式下的页码（默认：0）')
    parser.add_argument('--skip-crawl', action='store_true',
                       help='跳过爬取步骤，直接进行分析')
    parser.add_argument('--skip-analysis', action='store_true',
                       help='跳过分析步骤，只爬取数据')
    parser.add_argument('--skip-server', action='store_true',
                       help='跳过Web服务启动')

    args = parser.parse_args()

    # 确保 data 目录存在
    DATA_DIR.mkdir(exist_ok=True)

    # 1. 爬取数据
    if not args.skip_crawl:
        crawl_args = ['--mode', args.mode]
        if args.mode == 'local':
            crawl_args.extend(['--file', args.file])
        else:
            crawl_args.extend(['--group-id', args.group_id, '--page', str(args.page)])

        run_command("main.py", CRAWL_DIR, crawl_args)

    # 2. 情感分析
    if not args.skip_analysis:
        run_command("run_analysis.py", ANALYZE_DIR)

    # 3. 启动Web服务
    if not args.skip_server:
        run_command("api_server.py", ANALYZE_DIR)


if __name__ == "__main__":
    main()
