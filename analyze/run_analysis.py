"""
快速运行情感分析
"""
import json
import sys
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sentiment_analyzer import SentimentAnalyzer


def main():
    """主函数"""
    print("=" * 50)
    print("豆瓣帖子情感分析工具")
    print("=" * 50)
    
    # 创建分析器
    print("\n初始化分析器...")
    analyzer = SentimentAnalyzer()
    
    # 批量分析
    print("\n开始分析数据（使用多进程并行处理）...")
    # CPU密集型任务使用进程池（use_threading=False）
    result = analyzer.analyze_batch("../data", use_threading=False)
    
    # 保存结果（API服务器会使用这个缓存文件）
    output_file = Path(__file__).parent / "analysis_result.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 显示统计信息
    stats = result["overall_statistics"]
    print("\n" + "=" * 50)
    print("分析完成！")
    print("=" * 50)
    print(f"\n📊 统计信息：")
    print(f"  总帖子数: {stats['total_posts']}")
    print(f"  总评论数: {stats['total_comments']}")
    print(f"  平均情感得分: {stats['avg_sentiment_score']:.4f}")
    print(f"\n📈 情感分布：")
    print(f"📈 情感分布：")
    if stats['total_comments'] > 0:
        dist = stats['sentiment_distribution']
        print(f"  正面: {dist['positive']} ({dist['positive'] / stats['total_comments'] * 100:.1f}%)")
        print(f"  中性: {dist['neutral']} ({dist['neutral'] / stats['total_comments'] * 100:.1f}%)")
        print(f"  负面: {dist['negative']} ({dist['negative'] / stats['total_comments'] * 100:.1f}%)")
        print(f"\n💾 结果已保存到: {output_file}")
        print("\n💡 提示：运行 'python api_server.py' 启动Web可视化界面")
    else:
        print("  没有数据可分析")


if __name__ == "__main__":
    main()

