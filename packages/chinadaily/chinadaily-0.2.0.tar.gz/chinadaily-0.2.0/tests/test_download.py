#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
人民日报PDF下载链接验证与测试工具
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse

# 添加详细日志配置
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("download_test.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# 动态导入download函数，防止循环导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chinadaily.chinadaily import download


def check_url_structure(url):
    """检查URL结构是否正确"""
    parsed = urlparse(url)
    
    # 检查基本结构
    if parsed.scheme != 'https':
        return False, "URL协议不是HTTPS"
    
    if parsed.netloc != 'paper.people.com.cn':
        return False, "URL域名不正确"
    
    # 检查是否包含正确的路径部分
    if '/rmrb/pc/attachement/' not in parsed.path:
        return False, "URL缺少/rmrb/pc/attachement/路径"
    
    return True, "URL结构正确"


def check_node_page_accessibility(date, max_nodes_to_check=5):
    """检查节点页面的可访问性"""
    import requests
    
    print("\n开始检查节点页面可访问性...")
    logger.info("开始检查节点页面可访问性")
    
    # 构建日期路径格式为 YYYY/MM/DD
    date_path = datetime.strftime(date, '%Y/%m/%d')
    accessible_nodes = []
    
    for i in range(1, max_nodes_to_check + 1):
        node_number = f"{i:02d}"
        node_url = f"https://paper.people.com.cn/rmrb/pc/layout/{date_path}/node_{node_number}.html"
        
        try:
            print(f"检查节点页面 {node_number}: {node_url}")
            response = requests.get(node_url, timeout=5)
            if response.ok:
                print(f"✓ 节点页面 {node_number} 可访问")
                accessible_nodes.append(node_number)
                logger.info(f"节点页面 {node_number} 可访问")
            else:
                print(f"✗ 节点页面 {node_number} 不可访问，状态码: {response.status_code}")
                logger.warning(f"节点页面 {node_number} 不可访问，状态码: {response.status_code}")
        except Exception as e:
            print(f"✗ 节点页面 {node_number} 访问出错: {e}")
            logger.error(f"节点页面 {node_number} 访问出错: {e}")
    
    print(f"\n找到 {len(accessible_nodes)} 个可访问的节点页面: {', '.join(accessible_nodes)}")
    logger.info(f"找到 {len(accessible_nodes)} 个可访问的节点页面: {', '.join(accessible_nodes)}")
    
    return accessible_nodes


def test_download():
    """测试下载功能，特别关注多节点页面PDF下载"""
    print("人民日报PDF下载测试工具")
    print("=" * 80)
    print("本工具用于测试增强后的PDF下载功能，特别是多节点页面的PDF提取")
    print("详细日志将保存到download_test.log文件")
    print("=" * 80)
    
    # 默认测试前一天的报纸（避免当天报纸可能还未发布）
    test_date = datetime.now() - timedelta(days=1)
    
    print(f"将测试下载 {test_date.strftime('%Y-%m-%d')} 的人民日报")
    print("如果需要测试其他日期，请在命令行参数中指定，格式为YYYYMMDD")
    print("例如: python test_download.py 20251013")
    print("=" * 80)
    
    # 检查是否有命令行参数指定日期
    if len(sys.argv) > 1:
        try:
            test_date = datetime.strptime(sys.argv[1], "%Y%m%d")
            print(f"已指定日期: {test_date.strftime('%Y-%m-%d')}")
            logger.info(f"测试日期已指定为: {test_date.strftime('%Y-%m-%d')}")
        except ValueError:
            print("日期格式错误，使用默认日期")
            logger.error(f"日期格式错误: {sys.argv[1]}, 使用默认日期")
    
    # 显示系统信息
    print(f"\n当前系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    logger.info(f"系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python版本: {sys.version}")
    
    # 检查节点页面可访问性
    accessible_nodes = check_node_page_accessibility(test_date, max_nodes_to_check=5)
    
    # 模拟URL结构测试
    print("\n开始模拟URL结构测试...")
    
    # 构建正确和错误的URL示例进行测试
    correct_url = f"https://paper.people.com.cn/rmrb/pc/attachement/{test_date.year}/{test_date.month:02d}/{test_date.day:02d}/sample.pdf"
    incorrect_url1 = f"https://paper.people.com.cn/attachement/{test_date.year}/{test_date.month:02d}/{test_date.day:02d}/sample.pdf"
    incorrect_url2 = f"http://paper.people.com.cn/rmrb/pc/attachement/{test_date.year}/{test_date.month:02d}/{test_date.day:02d}/sample.pdf"
    
    # 测试URL结构
    for url in [correct_url, incorrect_url1, incorrect_url2]:
        is_valid, message = check_url_structure(url)
        status = "✓ 有效" if is_valid else "✗ 无效"
        print(f"{status} - {url}")
        print(f"  原因: {message}")
        logger.info(f"URL测试 - {url}: {'有效' if is_valid else '无效'} ({message})")
    
    print("\nURL结构测试完成，现在执行实际下载测试...")
    logger.info("URL结构测试完成，开始执行实际下载测试")
    
    # 执行下载测试
    print(f"\n开始下载 {test_date.strftime('%Y-%m-%d')} 的人民日报...")
    logger.info(f"开始下载 {test_date.strftime('%Y-%m-%d')} 的人民日报")
    start_time = time.time()
    
    result = download(test_date, force=True)  # 强制重新下载
    
    end_time = time.time()
    
    print(f"\n下载耗时: {end_time - start_time:.2f} 秒")
    logger.info(f"下载耗时: {end_time - start_time:.2f} 秒")
    
    if result:
        print(f"\n测试成功！")
        logger.info("下载测试成功")
        print(f"报纸已成功下载并保存为: {result}")
        logger.info(f"报纸已成功下载并保存为: {result}")
        
        # 检查文件是否存在且大小合理
        if os.path.exists(result):
            file_size = os.path.getsize(result) / (1024 * 1024)  # MB
            print(f"文件大小: {file_size:.2f} MB")
            logger.info(f"文件大小: {file_size:.2f} MB")
            
            # 根据可访问节点数量判断文件大小是否合理
            expected_min_size = max(1, len(accessible_nodes) * 0.5)  # 每个节点至少0.5MB
            if file_size < expected_min_size:
                print(f"警告: 文件大小异常小（预期至少 {expected_min_size} MB），可能下载不完整")
                logger.warning(f"文件大小异常小（预期至少 {expected_min_size} MB），可能下载不完整")
            else:
                print("文件大小正常")
                logger.info("文件大小正常")
    else:
        print(f"\n测试失败！")
        logger.error("下载测试失败")
        print(f"无法下载 {test_date.strftime('%Y-%m-%d')} 的人民日报")
        logger.error(f"无法下载 {test_date.strftime('%Y-%m-%d')} 的人民日报")
        
        print("\n可能的原因:")
        print("1. 网站结构再次发生变化")
        print("2. 指定日期的报纸不存在或无法访问")
        print("3. 网络连接问题")
        print("4. URL规范化逻辑仍需调整")
        print("5. 多节点页面遍历逻辑有问题")
        
        logger.error("可能的失败原因: 网站结构变化、报纸不存在、网络问题、URL规范化逻辑问题或多节点页面遍历逻辑问题")
        
    print("\n测试完成")
    logger.info("测试完成")
    
    # 提供进一步测试的建议
    print("\n进一步测试建议:")
    print("- 查看download_test.log文件获取详细日志")
    print("- 尝试测试不同日期的报纸")
    print("- 检查日志输出中的节点页面访问情况")
    print("- 检查日志输出中的URL格式是否正确")
    print("- 如果问题依然存在，可能需要进一步调整URL解析逻辑或多节点页面遍历逻辑")
    print("- 手动检查下载函数中的节点页面遍历和URL构建逻辑")
    

if __name__ == "__main__":
    test_download()