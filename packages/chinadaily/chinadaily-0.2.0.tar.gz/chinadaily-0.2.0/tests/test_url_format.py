import os
import datetime
from chinadaily import download

# 测试生成的URL格式
if __name__ == "__main__":
    # 使用当前日期进行测试
    today = datetime.datetime.today()
    date = datetime.datetime(today.year, today.month, today.day)
    
    # 打印日期路径格式，验证是否为YYYY-MM-DD
    fmt_path = '%Y-%m-%d'
    date_path = datetime.datetime.strftime(date, fmt_path)
    print(f"日期路径格式: {date_path}")
    
    # 生成一个示例节点URL
    node_number = "01"
    node_url = f"https://paper.people.com.cn/rmrb/pc/layout/{date_path}/node_{node_number}.html"
    print(f"示例节点URL: {node_url}")
    
    # 生成一个示例PDF URL
    attachment_base_url = "https://paper.people.com.cn/rmrb/pc/attachement/"
    pdf_filename = f"rmrb{date.strftime('%Y%m%d')}_01.pdf"
    pdf_url = f"{attachment_base_url}{date_path}/{pdf_filename}"
    print(f"示例PDF URL: {pdf_url}")
    
    # 提示用户可以通过实际运行download函数来进一步测试
    print("\n注意：以上仅为URL格式测试。要实际测试URL是否有效，可以取消下面代码的注释并运行。")
    # try:
    #     # 实际调用download函数测试
    #     print("\n尝试调用download函数...")
    #     result = download(date, force=True)
    #     print(f"download函数调用结果: {result}")
    # except Exception as e:
    #     print(f"测试过程中遇到错误: {e}")