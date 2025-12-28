"""
服务启动脚本
"""
import argparse
import os
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NXZ NLU Service")
    parser.add_argument(
        "--test-ui",
        action="store_true",
        default=True,  # 默认启用
        help="启用 API 测试界面（默认启用，使用 --no-test-ui 禁用）"
    )
    parser.add_argument(
        "--no-test-ui",
        dest="test_ui",
        action="store_false",
        help="禁用 API 测试界面"
    )
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        help="禁用代理（如果遇到代理连接错误，使用此选项）"
    )
    parser.add_argument(
        "--hf-mirror",
        type=str,
        default=None,
        help="指定 HuggingFace 镜像源（例如：https://hf-mirror.com）"
    )
    args = parser.parse_args()
    
    # 处理代理设置
    if args.no_proxy:
        # 清除代理环境变量
        for proxy_var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
            if proxy_var in os.environ:
                del os.environ[proxy_var]
        print("ℹ️  已禁用代理设置\n")
    
    # 设置 HuggingFace 镜像源
    if args.hf_mirror:
        os.environ["HF_ENDPOINT"] = args.hf_mirror
        print(f"ℹ️  使用 HuggingFace 镜像源: {args.hf_mirror}\n")
    elif "HF_ENDPOINT" not in os.environ:
        # 默认使用镜像源（如果网络无法访问 huggingface.co）
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print("ℹ️  使用 HuggingFace 镜像源: https://hf-mirror.com")
        print("   提示：如果遇到网络问题，可以使用 --no-proxy 禁用代理，或使用 --hf-mirror 指定其他镜像源\n")
    
    # 将测试界面标志传递给应用
    os.environ["ENABLE_TEST_UI"] = str(args.test_ui).lower()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

