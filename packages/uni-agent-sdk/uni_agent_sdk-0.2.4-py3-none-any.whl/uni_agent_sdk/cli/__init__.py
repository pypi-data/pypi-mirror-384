"""命令行工具入口"""


def main():
    """主命令行入口函数"""
    import sys

    from .app import cli_app

    try:
        cli_app()
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
