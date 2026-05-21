# AI 股票分析面板 (AI Stock Analysis Panel)

## 📌 项目简介
本项目是一个基于 AI 的全栈股票分析应用。用户输入股票代码后，系统会通过调用大语言模型（LLM）获取实时联网行情数据，进行基本面分析，并严格以 JSON 格式返回“业务总结 (summary)”、“市场情绪 (sentiment)”和“风险等级 (risk_level)”，最终将分析结果持久化存储到 Supabase 数据库中。

---

## 交付清单 (Deliverables)

### 1. 在线访问 URL
- **Live Demo:** [👉 点击访问 AI 股票分析面板](https://your-app-name.onrender.com) *(⚠️ 提交前请将此处替换为你在 Render.com 上的实际部署链接)*
- **GitHub Repository:** [👉 点击访问源码](https://github.com/ssnsja/AIstock) *(⚠️ 请替换为你的 GitHub 仓库链接)*

### 2. Prompt 代码与 LLM JSON 强制格式化策略
为了确保 LLM 稳定且严格地输出符合前端要求的 JSON 数据格式，不仅在 Prompt 中明确了结构，还在 API 调用层开启了原生 JSON 模式（JSON Mode）。

prompt = f"""你是一个资深的华尔街股票分析师。用户查询了股票代码：{ticker}。
请基于联网信息中对该公司的了解，给出基本面分析。

请务必严格返回一段纯 JSON 格式的数据（不要包含任何 markdown 符号或额外的文字），必须包含以下 4 个字段：
{{
    "price": (请填入一个预估的近期大概股价，必须是浮点数数字，例如 150.5),
    "summary": "关于该公司的核心业务总结、近期可能的市场趋势分析（约 100 字）",
    "sentiment": "市场情绪（只能从 '乐观', '悲观', '中立' 中选一个）",
    "risk_level": "风险等级（只能从 '高', '中', '低' 中选一个）"
}}

response_format={'type': 'json_object'}输入这行可以使得大模型严格输出JSON格式数据。

## Debug 记录 (真实开发踩坑实录)

在开发过程中遇到了多个网络、数据库和类型校验相关的 Bug。以下是使用 AI 辅助解决的最具代表性的 3 个问题：

### 🔴 Bug 1: 代理冲突导致大模型 API 报 SSL 错误

* **报错信息:** `HTTPSConnectionPool... ProxyError('Unable to connect to proxy', SSLError)`
* **问题分析:** 本地开启了科学上网代理，导致 Python `requests` 底层在请求国内的阿里云 DashScope API 时发生 SSL 握手违规。
* **解决方案:** 在代码最顶层加入防御性“代理白名单”补丁，强制通义千问 API 直连，不走代理。

```python
import os
os.environ['NO_PROXY'] = 'dashscope.aliyuncs.com'
```

### 🔴 Bug 2: Supabase 路径双重重叠导致 500 错误 (PGRST125)

* **报错信息:** `{'code': 'PGRST125', 'message': 'Invalid path specified in request URL'}`
* **问题分析:** Supabase 官方 SDK 会自动拼接 `/rest/v1/`，但 `.env` 环境变量中不小心多带了这个后缀，导致请求 URL 变成了 `.../rest/v1//rest/v1/`，引发数据库网关拒绝访问。
* **解决方案:** 编写自动清洗防御代码，每次连接数据库前剥离多余路径和斜杠，彻底解决时空悖论和缓存干扰。

```python
raw_url = os.environ.get("SUPABASE_URL", "")
clean_url = raw_url.replace("/rest/v1/", "").rstrip("/")
```
### 🔴 Bug 3: Pydantic 校验拦截 LLM 的中文返回

* **报错信息:** `fastapi.exceptions.ResponseValidationError: Input should be 'Bullish', 'Neutral' or 'Bearish', 'input': '乐观'`
* **问题分析:** 数据库存储和大模型返回都已经成功，但 FastAPI 返回给前端前，`models.py` 中的 `Literal` 被写死了只能是英文枚举，导致中文的“乐观”触发了 500 服务器内部错误。
* **解决方案:** 将 Response Model 中的字段类型从严苛的 `Literal` 降级为 `str`，提升系统的鲁棒性，完美放行中文 JSON。