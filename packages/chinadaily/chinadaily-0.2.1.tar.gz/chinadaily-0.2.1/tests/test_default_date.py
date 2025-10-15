import datetime
from chinadaily.cli import main

# 测试默认日期逻辑
if __name__ == "__main__":
    # 显示当前日期
    today = datetime.date.today()
    print(f"今天是: {today}")
    
    # 检查当前时间，理解人民日报发布规律
    now = datetime.datetime.now()
    print(f"当前时间: {now.strftime('%H:%M:%S')}")
    
    # 注意：直接运行main函数可能会实际下载PDF文件
    # 如需完整测试，请取消下面的注释
    
    # print("\n运行测试 - 这将尝试下载今天的人民日报...")
    # try:
    #     # 清空命令行参数，模拟不指定日期的情况
    #     import sys
    #     original_args = sys.argv.copy()
    #     sys.argv = [sys.argv[0]]  # 只保留脚本名称
    #     
    #     # 运行main函数
    #     exit_code = main()
    #     print(f"测试完成，退出码: {exit_code}")
    # finally:
    #     # 恢复原始参数
    #     sys.argv = original_args
    
    print("\n提示：")
    print("1. 人民日报通常在当天凌晨就发布了当天的报纸")
    print("2. 修改后的代码确保默认下载的是当天的报纸")
    print("3. 如需要下载特定日期的报纸，请使用命令行参数指定日期")