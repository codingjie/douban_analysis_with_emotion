"""
情感分析模块
对豆瓣帖子进行多维度情感分析
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter, defaultdict
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from functools import partial
import jieba
import jieba.analyse
from snownlp import SnowNLP
import multiprocessing


# 模块级函数，用于多进程处理（必须定义在类外部以便pickle序列化）
def _process_file_worker(json_file_path):
    """处理单个文件（用于多进程）"""
    try:
        json_file = Path(json_file_path)
        with open(json_file, 'r', encoding='utf-8') as f:
            post_data = json.load(f)
        
        # 创建新的分析器实例（避免多进程冲突）
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_post(post_data)
        return result, None
    except Exception as e:
        return None, str(e)


class SentimentAnalyzer:
    """情感分析器"""
    
    def __init__(self):
        """初始化分析器"""
        # 加载停用词
        self.stopwords = self._load_stopwords()
        # 初始化jieba
        jieba.initialize()
    
    def _load_stopwords(self) -> set:
        """加载停用词表"""
        stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', 
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', 
            '自己', '这', '那', '吗', '呢', '啊', '吧', '呀', '哦', '嗯', '哈', '呵', '唉',
            '什么', '怎么', '为什么', '如何', '多少', '哪个', '哪些', '这个', '那个',
            '因为', '所以', '但是', '如果', '虽然', '然而', '不过', '而且', '或者',
            '他', '她', '它', '他们', '她们', '它们', '我们', '你们', '大家', '别人'
        }
        return stopwords
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        分析文本情感（优化版）
        
        Args:
            text: 文本内容
        
        Returns:
            包含情感得分和分类的字典
            {
                "score": 0.5,  # 情感得分 0-1，0.5以上为正面，以下为负面
                "sentiment": "positive/negative/neutral",  # 情感分类
                "intensity": 0.5  # 情感强度 0-1
            }
        """
        if not text or not text.strip():
            return {
                "score": 0.5,
                "sentiment": "neutral",
                "intensity": 0.0
            }
        
        # 限制文本长度以提高性能（SnowNLP处理长文本较慢）
        if len(text) > 2000:
            text = text[:2000]
        
        try:
            s = SnowNLP(text)
            score = s.sentiments  # 0-1之间的分数，越接近1越正面
            
            # 计算情感强度（距离0.5的距离）
            intensity = abs(score - 0.5) * 2
            
            # 分类情感
            if score > 0.6:
                sentiment = "positive"
            elif score < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "score": round(score, 4),
                "sentiment": sentiment,
                "intensity": round(intensity, 4)
            }
        except Exception as e:
            print(f"情感分析出错: {e}")
            return {
                "score": 0.5,
                "sentiment": "neutral",
                "intensity": 0.0
            }
    
    def extract_keywords(self, text: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        提取关键词（优化版）
        
        Args:
            text: 文本内容
            top_k: 返回前k个关键词
        
        Returns:
            关键词列表，每个包含词和权重
        """
        if not text or not text.strip():
            return []
        
        # 限制文本长度以提高性能
        if len(text) > 5000:
            text = text[:5000]
        
        try:
            # 使用TF-IDF提取关键词，使用idf文件加速
            keywords = jieba.analyse.extract_tags(text, topK=min(top_k, 30), withWeight=True, allowPOS=('n', 'v', 'a'))
            return [
                {"word": word, "weight": round(weight, 4)}
                for word, weight in keywords
            ]
        except Exception as e:
            print(f"关键词提取出错: {e}")
            return []
    
    def analyze_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个帖子
        
        Args:
            post_data: 帖子JSON数据
        
        Returns:
            分析结果
        """
        # 分析帖子内容
        post_content = post_data.get("post", {}).get("content", "")
        post_sentiment = self.analyze_sentiment(post_content)
        post_keywords = self.extract_keywords(post_content)
        
        # 分析所有评论（优化：批量处理）
        comments = post_data.get("comments", [])
        comment_sentiments = []
        comment_keywords_list = []
        author_sentiments = defaultdict(list)
        time_sentiments = []
        
        # 过滤空内容评论
        valid_comments = [c for c in comments if c.get("content", "").strip()]
        
        # 批量提取关键词（减少调用次数）
        all_comment_text = "\n".join([c.get("content", "") for c in valid_comments])
        if all_comment_text:
            comment_keywords_list = self.extract_keywords(all_comment_text, top_k=20)
        
        # 处理评论（限制数量以提高性能）
        max_comments = min(len(valid_comments), 100)  # 最多处理100条评论
        
        for comment in valid_comments[:max_comments]:
            content = comment.get("content", "")
            if not content:
                continue
            
            # 评论情感分析
            sentiment = self.analyze_sentiment(content)
            sentiment["comment_id"] = comment.get("comment_id", "")
            sentiment["author_id"] = comment.get("author", {}).get("id", "")
            sentiment["author_name"] = comment.get("author", {}).get("name", "")
            sentiment["publish_time"] = comment.get("publish_time", "")
            sentiment["like_count"] = comment.get("like_count", 0)
            comment_sentiments.append(sentiment)
            
            # 按作者统计情感
            author_id = comment.get("author", {}).get("id", "")
            if author_id:
                author_sentiments[author_id].append(sentiment["score"])
            
            # 按时间统计情感
            publish_time = comment.get("publish_time", "")
            if publish_time:
                try:
                    # 解析时间
                    time_obj = datetime.strptime(publish_time, "%Y-%m-%d %H:%M:%S")
                    time_sentiments.append({
                        "time": publish_time,
                        "timestamp": time_obj.timestamp(),
                        "score": sentiment["score"],
                        "sentiment": sentiment["sentiment"]
                    })
                except:
                    pass
        
        # 统计整体情感分布
        sentiment_distribution = Counter([s["sentiment"] for s in comment_sentiments])
        
        # 计算平均情感得分
        if comment_sentiments:
            avg_score = sum(s["score"] for s in comment_sentiments) / len(comment_sentiments)
        else:
            avg_score = post_sentiment["score"]
        
        # 按作者统计平均情感
        author_avg_sentiments = {}
        for author_id, scores in author_sentiments.items():
            author_avg_sentiments[author_id] = {
                "avg_score": round(sum(scores) / len(scores), 4),
                "count": len(scores)
            }
        
        # 合并所有关键词并统计
        all_keywords = post_keywords + comment_keywords_list
        keyword_counter = Counter()
        for kw in all_keywords:
            keyword_counter[kw["word"]] += kw["weight"]
        
        top_keywords = [
            {"word": word, "weight": round(weight, 4)}
            for word, weight in keyword_counter.most_common(30)
        ]
        
        return {
            "post_info": {
                "post_id": post_data.get("post", {}).get("post_id", ""),
                "title": post_data.get("post", {}).get("title", ""),
                "sentiment": post_sentiment,
                "keywords": post_keywords
            },
            "overall_statistics": {
                "total_comments": len(comments),
                "avg_sentiment_score": round(avg_score, 4),
                "sentiment_distribution": {
                    "positive": sentiment_distribution.get("positive", 0),
                    "negative": sentiment_distribution.get("negative", 0),
                    "neutral": sentiment_distribution.get("neutral", 0)
                }
            },
            "comment_sentiments": comment_sentiments,
            "author_sentiments": author_avg_sentiments,
            "time_sentiments": sorted(time_sentiments, key=lambda x: x["timestamp"]),
            "top_keywords": top_keywords
        }
    
    def analyze_batch(self, data_dir: str = "data", max_workers: int = None, use_threading: bool = False) -> Dict[str, Any]:
        """
        批量分析多个帖子（并行处理）
        
        Args:
            data_dir: 数据目录路径
            max_workers: 最大工作线程/进程数，None表示自动检测
            use_threading: 是否使用线程池（False默认使用进程池，True使用线程池）
                          CPU密集型任务应使用进程池（False），IO密集型任务使用线程池（True）
        
        Returns:
            批量分析结果
        """
        from tqdm import tqdm
        
        data_path = Path(data_dir)
        json_files = list(data_path.glob("*.json"))
        
        if not json_files:
            return {
                "overall_statistics": {
                    "total_posts": 0,
                    "total_comments": 0,
                    "avg_sentiment_score": 0.5,
                    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                    "posts_by_sentiment": {"positive": [], "negative": [], "neutral": []}
                },
                "top_keywords": [],
                "posts": []
            }
        
        # 自动检测工作线程数
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), len(json_files), 8)
        
        all_results = []
        overall_stats = {
            "total_posts": 0,
            "total_comments": 0,
            "sentiment_scores": [],
            "sentiment_distribution": Counter(),
            "all_keywords": Counter(),
            "posts_by_sentiment": defaultdict(list)
        }
        
        # 使用线程池或进程池并行处理
        # CPU密集型任务（情感分析、关键词提取）应使用进程池
        executor_class = ThreadPoolExecutor if use_threading else ProcessPoolExecutor
        
        print(f"使用{'线程' if use_threading else '进程'}池并行处理 {len(json_files)} 个文件（{max_workers}个并发）...")
        print(f"提示：{'线程池适合IO密集型任务' if use_threading else '进程池适合CPU密集型任务（情感分析、关键词提取）'}")
        
        # 选择处理函数（多进程使用模块级函数，多线程可以使用局部函数）
        if use_threading:
            # 线程池可以使用局部函数
            def process_file(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        post_data = json.load(f)
                    analyzer = SentimentAnalyzer()
                    result = analyzer.analyze_post(post_data)
                    return result, None
                except Exception as e:
                    return None, str(e)
            process_func = process_file
            file_args = json_files
        else:
            # 进程池必须使用模块级函数
            process_func = _process_file_worker
            file_args = [str(json_file) for json_file in json_files]
        
        with executor_class(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(process_func, file_arg): json_files[i]
                for i, file_arg in enumerate(file_args)
            }
            
            # 使用tqdm显示进度
            for future in tqdm(as_completed(future_to_file), total=len(json_files), desc="分析进度"):
                json_file = future_to_file[future]
                try:
                    result, error = future.result()
                    if error:
                        print(f"\n分析文件 {json_file.name} 时出错: {error}")
                        continue
                    
                    if result:
                        all_results.append(result)
                        
                        # 累计统计
                        overall_stats["total_posts"] += 1
                        overall_stats["total_comments"] += result["overall_statistics"]["total_comments"]
                        overall_stats["sentiment_scores"].append(result["overall_statistics"]["avg_sentiment_score"])
                        
                        # 情感分布
                        dist = result["overall_statistics"]["sentiment_distribution"]
                        overall_stats["sentiment_distribution"]["positive"] += dist["positive"]
                        overall_stats["sentiment_distribution"]["negative"] += dist["negative"]
                        overall_stats["sentiment_distribution"]["neutral"] += dist["neutral"]
                        
                        # 关键词
                        for kw in result["top_keywords"]:
                            overall_stats["all_keywords"][kw["word"]] += kw["weight"]
                        
                        # 按情感分类帖子
                        avg_score = result["overall_statistics"]["avg_sentiment_score"]
                        if avg_score > 0.6:
                            overall_stats["posts_by_sentiment"]["positive"].append(result["post_info"]["post_id"])
                        elif avg_score < 0.4:
                            overall_stats["posts_by_sentiment"]["negative"].append(result["post_info"]["post_id"])
                        else:
                            overall_stats["posts_by_sentiment"]["neutral"].append(result["post_info"]["post_id"])
                except Exception as e:
                    print(f"\n处理文件 {json_file.name} 时出错: {e}")
                    continue
        
        # 计算总体平均情感得分
        if overall_stats["sentiment_scores"]:
            overall_avg_score = sum(overall_stats["sentiment_scores"]) / len(overall_stats["sentiment_scores"])
        else:
            overall_avg_score = 0.5
        
        # 获取总体关键词
        top_keywords = [
            {"word": word, "weight": round(weight, 4)}
            for word, weight in overall_stats["all_keywords"].most_common(50)
        ]
        
        return {
            "overall_statistics": {
                "total_posts": overall_stats["total_posts"],
                "total_comments": overall_stats["total_comments"],
                "avg_sentiment_score": round(overall_avg_score, 4),
                "sentiment_distribution": dict(overall_stats["sentiment_distribution"]),
                "posts_by_sentiment": dict(overall_stats["posts_by_sentiment"])
            },
            "top_keywords": top_keywords,
            "posts": all_results
        }


if __name__ == "__main__":
    # 测试代码
    analyzer = SentimentAnalyzer()
    
    # 测试单个文件
    test_file = Path("data/16_355670360.json")
    if test_file.exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result = analyzer.analyze_post(data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 批量分析
    print("\n开始批量分析...")
    batch_result = analyzer.analyze_batch("data")

    # 保存结果
    output_file = Path(__file__).parent / "analysis_result.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(batch_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析完成！结果已保存到: {output_file}")
    print(f"共分析 {batch_result['overall_statistics']['total_posts']} 个帖子")
    print(f"共 {batch_result['overall_statistics']['total_comments']} 条评论")
    print(f"平均情感得分: {batch_result['overall_statistics']['avg_sentiment_score']}")

