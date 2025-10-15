"""Console script for chinadaily."""
import sys
# 添加urllib3兼容性修复（在导入requests之前）
sys.path.append('..')
try:
    import urllib3_compatibility
    urllib3_compatibility.ensure_urllib3_compatibility()
except ImportError:
    # 如果无法导入兼容性修复模块，继续执行
    pass

import argparse
from datetime import datetime

from .constants import CLI_DATE_FORMAT, CLI_MONTH_FORMAT, CLI_YEAR_FORMAT
from .chinadaily import download


# todo(@yarving): auto generate version number
def get_version():
    """Get version number"""
    return '0.2.0'


def get_parser():
    """Get argument parser"""
    parser = argparse.ArgumentParser("China Daily newspaper downloader")
    parser.add_argument(
        'date', nargs='*',
        type=lambda s: datetime.strptime(s, CLI_DATE_FORMAT),
        help="default as today, multiple dates separated by blank")
    parser.add_argument(
        "-m", "--month",
        type=lambda s: datetime.strptime(s, CLI_MONTH_FORMAT),
        help="download a month's newspaper")
    parser.add_argument(
        "-y", "--year",
        type=lambda s: datetime.strptime(s, CLI_YEAR_FORMAT),
        help="download a year's newspaper")
    parser.add_argument(
        '-v', '--version',
        action='version', version=get_version(), help='Display version')
    parser.add_argument(
        "-f", "--force", help="force to re-write", action="store_true", default=False)

    return parser


def main():
    """Console script for chinadaily."""
    parser = get_parser()
    args = parser.parse_args()

    # 处理默认日期，考虑人民日报发布时间规律
    if args.date:
        dates = args.date
    else:
        # 获取当前日期和时间
        now = datetime.now()
        # 由于人民日报通常在当天凌晨就发布了第二天的报纸
        # 所以默认下载当天的报纸
        dates = [datetime(now.year, now.month, now.day)]
    success_count = 0
    fail_count = 0
    
    for date in dates:
        print(f"\n尝试下载 {date.strftime('%Y-%m-%d')} 的人民日报...")
        result = download(date, force=args.force)
        if result:
            success_count += 1
            print(f"下载成功: {result}")
        else:
            fail_count += 1
            print(f"下载失败: {date.strftime('%Y-%m-%d')}")
    
    print(f"\n下载完成: 成功 {success_count} 个, 失败 {fail_count} 个")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
