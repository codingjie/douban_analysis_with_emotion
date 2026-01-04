#!/bin/bash

# 豆瓣帖子爬虫与情感分析系统 - 交互式启动脚本

echo "========================================"
echo "  豆瓣帖子爬虫与情感分析系统"
echo "========================================"
echo ""
echo "请选择爬取模式："
echo "1. 本地模式 - 爬取本地HTML文件"
echo "2. 远程模式 - 从豆瓣网站爬取（默认）"
echo ""
read -p "请输入选项 (1/2) [默认: 2]: " mode_choice

# 如果用户没有输入，默认为2
mode_choice=${mode_choice:-2}

if [ "$mode_choice" == "1" ]; then
    # 本地模式
    echo ""
    read -p "请输入本地HTML文件路径 [默认: response.html]: " html_file
    html_file=${html_file:-response.html}

    echo ""
    echo "开始执行本地模式..."
    python3 run.py --mode local --file "$html_file"

elif [ "$mode_choice" == "2" ]; then
    # 远程模式
    echo ""
    read -p "请输入小组ID [默认: 724338]: " group_id
    group_id=${group_id:-724338}

    read -p "请输入页码 [默认: 0]: " page
    page=${page:-0}

    echo ""
    echo "开始执行远程模式..."
    python3 run.py --mode remote --group-id "$group_id" --page "$page"

else
    echo "无效的选项，退出。"
    exit 1
fi

echo ""
echo "========================================"
echo "  执行完成！"
echo "========================================"
