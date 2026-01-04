"""
豆瓣帖子爬虫与情感分析系统 - 一键运行脚本
"""
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.absolute()
CRAWL_DIR = ROOT_DIR / "crawl"
ANALYZE_DIR = ROOT_DIR / "analyze"
DATA_DIR = ROOT_DIR / "data"


def run_command(script_name, cwd):
    """运行Python脚本"""
    subprocess.run([sys.executable, script_name], cwd=cwd)


def main():
    # 确保 data 目录存在
    DATA_DIR.mkdir(exist_ok=True)

    # 1. 爬取数据
    run_command("main.py", CRAWL_DIR)

    # 2. 情感分析
    run_command("run_analysis.py", ANALYZE_DIR)

    # 3. 启动Web服务
    run_command("api_server.py", ANALYZE_DIR)


if __name__ == "__main__":
    main()