import os
import json
import dashscope
from supabase import create_client
from typing import Any

# ================= 终极代理补丁 =================
# 告诉 Python：访问阿里云通义千问时，强制直连，绝对不要走 VPN 代理！
os.environ['NO_PROXY'] = 'dashscope.aliyuncs.com'
os.environ['no_proxy'] = 'dashscope.aliyuncs.com'
# ===============================================

def analyze_with_llm(ticker: str):
    """
    完全抛弃雅虎，直接让大模型基于常识生成分析结果和模拟价格
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    dashscope.api_key = "sk-4be50b7256bb472eaa1f11912ac1f824"
    prompt = f"""你是一个资深的华尔街股票分析师。用户查询了股票代码：{ticker}。
请基于联网信息中对该公司的了解，给出基本面分析。

请务必严格返回一段纯 JSON 格式的数据（不要包含任何 markdown 符号或额外的文字），必须包含以下 4 个字段：
{{
    "price": (请填入一个预估的近期大概股价，必须是浮点数数字，例如 150.5),
    "summary": "关于该公司的核心业务总结、近期可能的市场趋势分析（约 100 字）",
    "sentiment": "市场情绪（只能从 '乐观', '悲观', '中立' 中选一个）",
    "risk_level": "风险等级（只能从 '高', '中', '低' 中选一个）"
}}
"""
    
    # 调用通义千问大模型
    response:Any = dashscope.Generation.call(
        model=dashscope.Generation.Models.qwen_plus, # 升级到 plus 模型，效果更好
        prompt=prompt,
        result_format='message',
        response_format={'type': 'json_object'},
        enable_search=True
    )
    
    if response.status_code == 200:
        content = response.output.choices[0].message.content
        try:
            # 尝试清洗大模型可能带有的 ```json 标签
            clean_content = content.replace("```json", "").replace("```", "").strip()
            result_json = json.loads(clean_content)
            return result_json
        except json.JSONDecodeError:
            raise ValueError(f"大模型返回的格式不是合法 JSON: {content}")
    else:
        raise ValueError(f"大模型调用失败: {response.code} - {response.message}")

def save_analysis_to_db(ticker: str, price: float, analysis_result: dict):
    """
    将分析结果存入 Supabase（每次调用时动态加载并清洗 URL，彻底杜绝缓存和顺序问题）
    """
    # 1. 现场获取并暴力清洗 URL（绝不能有 /rest/v1/ 和尾部斜杠）
    raw_url = os.environ.get("SUPABASE_URL", "")
    clean_url = raw_url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
    
    # 2. 现场获取 Key
    key = os.environ.get("SUPABASE_KEY", "")
    
    # 3. 现场创建客户端连接
    supabase = create_client(clean_url, key)
    
    # 4. 组装数据并插入
    data = {
        "ticker": ticker.upper(),
        "current_price": price,
        "summary": analysis_result.get("summary", ""),
        "sentiment": analysis_result.get("sentiment", "中立"),
        "risk_level": analysis_result.get("risk_level", "中")
    }
    print(f"输出结果{data}")
    # 插入数据库
    # 明确告诉数据库：如果 ticker 发生重复冲突了，就执行更新！
    result = supabase.table("stock_analysis").upsert(
        data, 
        on_conflict="ticker"  #  加上这个参数
    ).execute()
    
    return result