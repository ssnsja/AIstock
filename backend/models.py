from pydantic import BaseModel, Field
from typing import Literal, Dict, Any

class AnalyzeRequest(BaseModel):
    ticker: str = Field(..., description="股票代码, 如 AAPL")


class AIAnalysisResult(BaseModel): # 保持你原来的类名不变
    summary: str
    sentiment: str  
    risk_level: str 

class AnalyzeResponse(BaseModel):
    ticker: str
    price: float
    analysis: AIAnalysisResult