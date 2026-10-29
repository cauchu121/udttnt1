from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import auth, policies, claims, finance, ai, analytics

# Tự động tạo các bảng CSDL khi khởi động nếu chưa tồn tại
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Hệ thống Quản lý Bảo hiểm Tích hợp AI (InsurTech Smart System) - Đồ án môn học Ứng dụng Trí tuệ Nhân tạo",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Cấu hình CORS an toàn cho Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chống lưu bộ nhớ đệm (Cache-Busting) cho Frontend Static Files
@app.middleware("http")
async def add_no_cache_header(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# 1. Global Exception Handler bắt lỗi nhập liệu Form qua Pydantic
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    formatted_errors = []
    for err in exc.errors():
        field = " -> ".join([str(x) for x in err.get("loc", [])])
        formatted_errors.append({"field": field, "message": err.get("msg", "")})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_code": "INVALID_INPUT_DATA",
            "message": "Dữ liệu nhập vào hồ sơ không đúng định dạng",
            "errors": formatted_errors
        }
    )

# 2. Global Exception Handler bắt lỗi thao tác Cơ sở dữ liệu CSDL
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_code": "DATABASE_ERROR",
            "message": "Hệ thống gặp sự cố thao tác dữ liệu bảo hiểm. Vui lòng thử lại sau!",
            "detail": str(exc)
        }
    )

# Đăng ký các Router nghiệp vụ
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(policies.router, prefix=settings.API_V1_STR)
app.include_router(claims.router, prefix=settings.API_V1_STR)
app.include_router(finance.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_endpoint():
    return {"status": "ok", "service": "InsurTech AI Backend"}

# Mount Frontend Web Portal Static Files
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
else:
    @app.get("/")
    def root_health_check():
        return {
            "system": settings.PROJECT_NAME,
            "status": "Online",
            "version": settings.VERSION,
            "ai_mock_mode": settings.AI_MOCK_MODE,
            "docs_url": "/docs"
        }
