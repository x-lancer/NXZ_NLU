"""
FastAPI应用主入口
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import router
from app.api.dependencies import initialize_nlu_service
from app.utils.logger import setup_logger

# 初始化日志
logger = setup_logger()

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="逆行者语义识别服务 - 自然语言理解服务，用于意图识别和标准化数据返回",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info("Loading NLU models and services...")
    # 初始化NLU服务
    initialize_nlu_service()
    logger.info("✅ NLU 服务初始化完成！")
    
    # 检查测试界面是否启用
    enable_test_ui = os.getenv("ENABLE_TEST_UI", "false").lower() == "true"
    if enable_test_ui:
        # 如果绑定到 0.0.0.0，提示用户使用服务器的实际 IP 或域名
        if settings.HOST == "0.0.0.0":
            logger.info("=" * 70)
            logger.info("🎉 API 测试界面已启用！")
            logger.info(f"📝 本地访问: http://localhost:{settings.PORT}/test-ui")
            logger.info(f"📝 服务器访问: http://<服务器IP或域名>:{settings.PORT}/test-ui")
            logger.info(f"   提示：请将 <服务器IP或域名> 替换为实际的服务器的 IP 地址或域名")
            logger.info("=" * 70)
            # 同时打印到控制台（确保用户能看到）
            print("\n" + "=" * 70)
            print("🎉 API 测试界面已启用！")
            print(f"📝 本地访问: http://localhost:{settings.PORT}/test-ui")
            print(f"📝 服务器访问: http://<服务器IP或域名>:{settings.PORT}/test-ui")
            print(f"   提示：请将 <服务器IP或域名> 替换为实际的服务器的 IP 地址或域名")
            print("=" * 70 + "\n")
        else:
            test_ui_url = f"http://{settings.HOST}:{settings.PORT}/test-ui"
            logger.info("=" * 70)
            logger.info("🎉 API 测试界面已启用！")
            logger.info(f"📝 访问地址: {test_ui_url}")
            logger.info("=" * 70)
            # 同时打印到控制台（确保用户能看到）
            print("\n" + "=" * 70)
            print("🎉 API 测试界面已启用！")
            print(f"📝 访问地址: {test_ui_url}")
            print("=" * 70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("Shutting down NLU service...")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }


# 测试界面路由（默认启用，可通过环境变量禁用）
@app.get("/test-ui")
async def test_ui():
    """API 测试界面 - 可视化 API 调试工具"""
    static_dir = Path(__file__).parent / "static"
    html_file = static_dir / "test-ui.html"
    if html_file.exists():
        return FileResponse(html_file, media_type="text/html")
    else:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail="测试界面文件未找到，请确保 app/static/test-ui.html 文件存在"
        )

