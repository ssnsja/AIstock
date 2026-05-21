from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import FileResponse
import uvicorn
from backend.models import AnalyzeRequest, AnalyzeResponse
from backend.services import analyze_with_llm, save_analysis_to_db

# 加载 .env 文件中的环境变量
load_dotenv()

app = FastAPI(title="AI Stock Analysis Panel API")

# 配置 CORS 解决前后端分离导致的跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中建议限制为前端实际域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
analyze_router = APIRouter()
app.include_router(analyze_router, prefix="/api")

# ================= 新增：前端托管 =================
# 2. 把根目录 "/" 绑定给你的 index.html
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_stock_endpoint(request: AnalyzeRequest):
    """
    纯大模型驱动的股票分析接口（已剔除雅虎请求）
    """
    try:
        # 1. 直接调用 LLM 进行推演
        analysis_result = analyze_with_llm(request.ticker)
        
        # 2. 从 LLM 返回的 JSON 中提取估算的价格，如果没有就默认 0.0
        mock_price = float(analysis_result.get("price", 0.0))
        
        # 为了前端展示干净，把 price 从 analysis 字典里拿出来，只留纯分析文本
        clean_analysis = {
            "summary": analysis_result.get("summary"),
            "sentiment": analysis_result.get("sentiment"),
            "risk_level": analysis_result.get("risk_level")
        }
        
        # 3. 数据存入 Supabase
        save_analysis_to_db(request.ticker, mock_price, clean_analysis)
        
        # 4. 返回前端所需结构
        return {
            "ticker": request.ticker.upper(),
            "price": mock_price,
            "analysis": clean_analysis
        }
    except ValueError as ve:
        # HTTP 400 通常用于表示客户端传参错误或业务逻辑预期的校验失败
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

# 新增程序入口
if __name__ == "__main__":
    # 使用 uvicorn 自动启动服务
    # 注意：因为使用了相对导入 (如 backend.models)，请确保在项目根目录运行此脚本
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)