"""CLI应用主逻辑"""

import argparse
import sys
from typing import Optional


def cli_app():
    """CLI应用主函数"""
    parser = argparse.ArgumentParser(
        prog="uni-agent",
        description="uni-agent-sdk 命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  uni-agent init my-agent           创建新的智能体项目
  uni-agent build                   构建智能体镜像
  uni-agent build --version 1.0.0   构建指定版本镜像
  uni-agent publish                 发布智能体到云端
  uni-agent publish --skip-build    跳过构建，直接发布现有镜像
  uni-agent run                     运行智能体
  uni-agent test                    运行测试
  uni-agent --version               显示版本信息
        """,
    )

    parser.add_argument("--version", action="version", version="uni_agent_sdk 0.2.0")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # init 命令
    init_parser = subparsers.add_parser("init", help="创建新的智能体项目")
    init_parser.add_argument("name", help="项目名称")
    init_parser.add_argument("--template", default="basic", help="项目模板")
    init_parser.add_argument(
        "--skip-venv",
        action="store_true",
        help="跳过虚拟环境创建和依赖安装",
    )

    # build 命令
    from .build import add_build_command

    add_build_command(subparsers)

    # publish 命令
    from .publish import add_publish_command

    add_publish_command(subparsers)

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行智能体容器并显示日志")
    run_parser.add_argument("--config", "-c", help="配置文件路径")
    run_parser.add_argument("--debug", action="store_true", help="启用调试模式")
    run_parser.add_argument("--port", "-p", type=int, default=None, help="主机端口（可选，不指定则不绑定端口）")

    # test 命令
    test_parser = subparsers.add_parser("test", help="运行测试")
    test_parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "init":
            from .commands import init_project

            success = init_project(
                args.name, args.template, skip_venv=args.skip_venv
            )
            sys.exit(0 if success else 1)
        elif args.command == "build":
            # build 命令使用 func 回调
            if hasattr(args, "func"):
                success = args.func(args)
                sys.exit(0 if success else 1)
            else:
                print("❌ build 命令未正确配置")
                sys.exit(1)
        elif args.command == "publish":
            # publish 命令使用 func 回调
            if hasattr(args, "func"):
                success = args.func(args)
                sys.exit(0 if success else 1)
            else:
                print("❌ publish 命令未正确配置")
                sys.exit(1)
        elif args.command == "run":
            from .commands import run_agent

            success = run_agent(args.config, args.debug, args.port)
            sys.exit(0 if success else 1)
        elif args.command == "test":
            from .commands import run_tests

            success = run_tests(args.verbose)
            sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"命令模块导入失败: {e}")
        print("请确保所有依赖已正确安装")
        sys.exit(1)
