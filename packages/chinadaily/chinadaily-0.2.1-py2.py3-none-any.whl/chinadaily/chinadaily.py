# -*- coding: utf-8 -*-
"""Main module."""

__author__ = "Yarving Liu"
__author_email__ = "yarving@qq.com"


import os
import re
import tempfile
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfFileReader, PdfFileWriter


def merge(files, filename):
    """ Merge PDF files in correct page order

    """
    writer = PdfFileWriter()
    
    # 按照文件名中的节点编号和序号排序文件
    def get_sort_key(file_path):
        file_name = os.path.basename(file_path)
        # 尝试从文件名中提取节点编号
        node_match = re.search(r'node(\d{2})', file_name)
        
        if node_match:
            return int(node_match.group(1))
        
        # 如果找不到节点编号，返回一个大值放在最后
        return 999
    
    # 对文件列表进行排序
    sorted_files = sorted(files, key=get_sort_key)
    print(f"按节点编号顺序合并文件: {[os.path.basename(f) for f in sorted_files]}")

    for f in sorted_files:
        pdf = PdfFileReader(open(f, "rb"), strict=False)

        # 分别将page添加到输出output中
        for page in range(pdf.getNumPages()):
            writer.addPage(pdf.getPage(page))

    with open(filename, "wb") as stream:
        writer.write(stream)


def download(date, force=False):
    """
    从人民日报网站下载指定日期的报纸PDF文件，新的实现方式是：
    1. 访问日期对应的所有版面HTML页面（node_01.html, node_02.html等）
    2. 从页面中提取所有PDF链接
    3. 下载这些PDF文件
    4. 合并它们为一个完整的PDF文件
    """
    # 修改日期路径格式为 YYYY-MM-DD，符合网站新的URL结构
    fmt_path = '%Y%m/%d'
    date_path = datetime.strftime(date, fmt_path)
    fmt_name = '%Y%m%d'
    file_prefix = datetime.strftime(date, fmt_name)

    outfile = f"rmrb{file_prefix}.pdf"
    if os.path.exists(outfile) and not force:
        print(f"{outfile} already exist, skip to download")
        return outfile

    print("downloading with requests")

    # 基础URL定义
    base_url = "https://paper.people.com.cn/rmrb/pc/"
    attachment_base_url = "https://paper.people.com.cn/rmrb/pc/attachement/"
    
    # 存储所有找到的PDF链接，格式为(节点编号, PDF链接)
    pdf_links_with_node = []
    
    # 尝试访问所有可能的节点页面，直到遇到404错误
    print("正在尝试访问所有节点页面以获取PDF链接...")
    max_nodes = 99  # 设置一个合理的最大节点数
    for i in range(1, max_nodes + 1):
        node_number = f"{i:02d}"
        node_url = f"https://paper.people.com.cn/rmrb/pc/layout/{date_path}/node_{node_number}.html"
        
        try:
            print(f"访问节点页面 {node_number}: {node_url}")
            response = requests.get(node_url, timeout=10)
            
            # 如果页面不存在(404)，停止尝试更多页面
            if response.status_code == 404:
                print(f"节点页面 {node_number} 不存在 (404)")
                # 但不要立即停止，因为可能还有后面的页面存在
                # 继续检查几个页面，确认是否真的没有更多页面了
                check_more = 3  # 再检查3个页面
                not_found_count = 1
                for j in range(i + 1, i + check_more + 1):
                    check_node_url = f"https://paper.people.com.cn/rmrb/pc/layout/{date_path}/node_{j:02d}.html"
                    check_response = requests.get(check_node_url, timeout=5)
                    if check_response.status_code == 404:
                        not_found_count += 1
                    else:
                        break  # 找到存在的页面，继续主循环
                
                # 如果连续几个页面都不存在，认为没有更多页面了
                if not_found_count > check_more / 2:
                    print(f"连续 {not_found_count} 个节点页面不存在，停止查找更多页面")
                    break
                else:
                    continue  # 继续检查更多页面
            
            # 如果返回其他错误状态码，跳过这个页面
            elif not response.ok:
                print(f"访问节点页面 {node_number} 失败，状态码: {response.status_code}")
                continue
            
            # 页面访问成功，开始解析
            print(f"成功访问节点页面 {node_number}")
            soup = BeautifulSoup(response.content, 'lxml')
            
            # 1. 从a标签中提取PDF链接
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf'):
                    # 确保是完整的URL
                    if not href.startswith('http'):
                        # 使用urljoin处理相对路径
                        full_url = urljoin(base_url, href)
                    else:
                        full_url = href
                    
                    # 确保URL包含/rmrb/pc/attachement/路径
                    if '/rmrb/pc/attachement/' not in full_url:
                        # 提取文件名部分
                        parsed_url = urlparse(full_url)
                        path_parts = parsed_url.path.split('/')
                        # 找到文件名部分
                        pdf_filename = next((part for part in path_parts if part.endswith('.pdf')), None)
                        if pdf_filename:
                            # 构建正确的URL
                            full_url = f"{attachment_base_url}{date_path}/{pdf_filename}"
                    
                    # 存储节点编号和PDF链接的对应关系
                    if full_url not in [link for _, link in pdf_links_with_node]:
                        pdf_links_with_node.append((node_number, full_url))
            
            # 2. 从script标签中提取PDF链接
            scripts = soup.find_all('script')
            pdf_pattern = r'https?://[^"\']+\.pdf'
            for script in scripts:
                if script.string:
                    found_links = re.findall(pdf_pattern, script.string)
                    for pdf_url in found_links:
                        # 确保URL包含/rmrb/pc/attachement/路径
                        if '/rmrb/pc/attachement/' not in pdf_url:
                            # 提取文件名部分
                            parsed_url = urlparse(pdf_url)
                            path_parts = parsed_url.path.split('/')
                            # 找到文件名部分
                            pdf_filename = next((part for part in path_parts if part.endswith('.pdf')), None)
                            if pdf_filename:
                                # 构建正确的URL
                                pdf_url = f"{attachment_base_url}{date_path}/{pdf_filename}"
                        
                        # 存储节点编号和PDF链接的对应关系
                        if pdf_url not in [link for _, link in pdf_links_with_node]:
                            pdf_links_with_node.append((node_number, pdf_url))
            
        except Exception as e:
            print(f"访问节点页面 {node_number} 时出错: {e}")
            # 出错时继续尝试下一个页面，但可能是网络问题，尝试几次后可以考虑退出
            continue
    
    # 打印找到的链接数量
    print(f"总共找到 {len(pdf_links_with_node)} 个PDF链接")
        
    # 清理和规范化所有链接，并保留节点编号信息
    normalized_links_with_node = []
    for node_number, link in pdf_links_with_node:
        # 确保URL包含/rmrb/pc/attachement/路径
        if '/rmrb/pc/attachement/' not in link:
            # 提取文件名部分
            parsed_url = urlparse(link)
            path_parts = parsed_url.path.split('/')
            # 找到文件名部分
            pdf_filename = next((part for part in path_parts if part.endswith('.pdf')), None)
            if pdf_filename:
                # 构建正确的URL
                link = f"{attachment_base_url}{date_path}/{pdf_filename}"
        
        # 解析URL并规范化路径（去除多余的../）
        parsed = urlparse(link)
        # 分割路径并处理
        path_parts = parsed.path.split('/')
        normalized_parts = []
        for part in path_parts:
            if part == '..':
                if normalized_parts and normalized_parts[-1] != '..':
                    normalized_parts.pop()
            else:
                normalized_parts.append(part)
        normalized_path = '/'.join(normalized_parts)
        # 重建URL
        normalized_url = urlunparse((parsed.scheme, parsed.netloc, normalized_path, parsed.params, parsed.query, parsed.fragment))
        normalized_links_with_node.append((node_number, normalized_url))
    
    # 去重但保留节点编号信息
    seen_links = set()
    unique_links_with_node = []
    for node_number, link in normalized_links_with_node:
        if link not in seen_links:
            seen_links.add(link)
            unique_links_with_node.append((node_number, link))
    
    pdf_links_with_node = unique_links_with_node
    
    print(f"找到 {len(pdf_links_with_node)} 个唯一的PDF链接")
    
    # 创建临时目录下载PDF文件
    temp_dir = tempfile.mkdtemp()
    files = []
    
    # 按照节点编号对PDF链接进行排序
    pdf_links_with_node.sort(key=lambda x: x[0])  # 按照节点编号排序
    
    # 下载所有PDF文件，文件名中包含节点编号
    for i, (node_number, pdf_url) in enumerate(pdf_links_with_node, 1):
        try:
            print(f"下载节点 {node_number} 的第 {i} 个PDF文件: {pdf_url}")
            r = requests.get(pdf_url)
            if r.ok:
                # 使用节点编号作为页面编号的基础
                
                # 生成文件名，包含节点编号和索引
                filename = f"rmrb{file_prefix}_node{node_number}_{i:02d}.pdf"
                output = os.path.join(temp_dir, filename)
                with open(output, "wb") as f:
                    f.write(r.content)
                files.append(output)
            else:
                print(f"下载失败，状态码: {r.status_code}")
        except Exception as e:
            print(f"下载出错: {e}")
    
    if not files:
        print("没有下载到任何PDF文件")
        return None
    
    # 合并所有PDF文件
    merge(files, outfile)
    print(f"已成功下载并合并为: {outfile}")

    return outfile
