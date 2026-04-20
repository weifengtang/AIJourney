#!/usr/bin/env python3
"""
/search - 搜索历史对话
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.base import collect_all
from datetime import date, timedelta


def main():
    # 获取搜索关键词
    if len(sys.argv) < 2:
        print("请提供搜索关键词")
        print("用法: /search <关键词>")
        return
    
    keyword = " ".join(sys.argv[1:])
    
    print(f"🔍 正在搜索: {keyword}")
    
    # 搜索最近7天的数据
    results = []
    today = date.today()
    
    for i in range(7):
        target_date = today - timedelta(days=i)
        sessions = collect_all(target_date)
        
        for session in sessions:
            # 在标题、摘要、消息内容中搜索
            search_text = f"{session.title} {session.summary}"
            for msg in session.messages:
                search_text += f" {msg.content}"
            
            if keyword.lower() in search_text.lower():
                results.append({
                    'date': target_date.strftime('%Y-%m-%d'),
                    'source': session.source,
                    'title': session.title,
                    'summary': session.summary,
                    'project_path': session.project_path,
                })
    
    # 显示结果
    if results:
        print(f"\n找到 {len(results)} 条匹配结果:\n")
        for idx, result in enumerate(results[:10], 1):
            print(f"{idx}. [{result['date']}] [{result['source']}]")
            print(f"   标题: {result['title']}")
            print(f"   摘要: {result['summary'][:150]}...")
            print()
    else:
        print("未找到匹配的结果")


if __name__ == "__main__":
    main()