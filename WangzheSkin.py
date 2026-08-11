import argparse
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from fake_useragent import UserAgent

HERO_LIST_URL: str = "https://pvp.qq.com/web201605/js/herolist.json"
SKIN_BASE_URL: str = "http://game.gtimg.cn/images/yxzj/img201606/skin/hero-info/{ename}/{ename}-bigskin-{skin_id}.jpg"
MAX_SKIN_COUNT: int = 10
DEFAULT_TIMEOUT: int = 10
MAX_RETRIES: int = 3


def fetch_hero_list(timeout: int = DEFAULT_TIMEOUT, retries: int = MAX_RETRIES) -> List[Dict]:
    """获取王者荣耀英雄列表数据

    Args:
        timeout: 请求超时时间（秒）
        retries: 失败重试次数

    Returns:
        英雄信息列表，每个元素包含 cname(英雄名称) 和 ename(英雄编号) 等字段

    Raises:
        RuntimeError: 多次重试后仍无法获取数据时抛出
    """
    ua = UserAgent()
    headers = {"User-Agent": ua.random}

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(HERO_LIST_URL, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            print(f"[警告] 获取英雄列表超时（第 {attempt}/{retries} 次尝试）")
        except requests.exceptions.RequestException as e:
            print(f"[警告] 获取英雄列表网络错误：{e}（第 {attempt}/{retries} 次尝试）")
        except ValueError as e:
            print(f"[错误] 英雄列表 JSON 解析失败：{e}")
            break
        if attempt < retries:
            time.sleep(1)

    raise RuntimeError("多次重试后仍无法获取英雄列表，请检查网络连接")


def download_image(url: str, save_path: Path, timeout: int = DEFAULT_TIMEOUT, retries: int = MAX_RETRIES) -> bool:
    """下载单张皮肤图片并保存

    Args:
        url: 图片下载链接
        save_path: 保存文件的完整路径
        timeout: 请求超时时间（秒）
        retries: 失败重试次数

    Returns:
        下载成功返回 True，失败返回 False
    """
    ua = UserAgent()
    headers = {"User-Agent": ua.random}

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                return True
            elif resp.status_code == 404:
                return False
            else:
                print(f"[警告] 下载图片状态码异常 {resp.status_code}：{save_path.name}（第 {attempt}/{retries} 次尝试）")
        except requests.exceptions.Timeout:
            print(f"[警告] 下载图片超时：{save_path.name}（第 {attempt}/{retries} 次尝试）")
        except requests.exceptions.RequestException as e:
            print(f"[警告] 下载图片网络错误：{e}（第 {attempt}/{retries} 次尝试）")
        except OSError as e:
            print(f"[错误] 写入文件失败 {save_path}：{e}")
            return False

        if attempt < retries:
            time.sleep(1)

    print(f"[错误] 图片下载失败：{save_path.name}")
    return False


def download_hero_skins(hero: Dict, output_dir: Path, timeout: int = DEFAULT_TIMEOUT,
                        retries: int = MAX_RETRIES, sleep_min: float = 1.0, sleep_max: float = 3.0) -> None:
    """下载单个英雄的所有皮肤图片

    Args:
        hero: 英雄信息字典，包含 cname 和 ename 字段
        output_dir: 根输出目录
        timeout: 单张图片请求超时时间（秒）
        retries: 单张图片失败重试次数
        sleep_min: 两次下载之间最小休眠时间（秒）
        sleep_max: 两次下载之间最大休眠时间（秒）
    """
    hero_name = hero.get("cname", "未知英雄")
    ename = hero.get("ename")
    if not ename:
        print(f"[跳过] 英雄数据缺少编号：{hero_name}")
        return

    hero_dir = output_dir / hero_name
    hero_dir.mkdir(parents=True, exist_ok=True)

    print(f"[开始] 下载英雄：{hero_name}")
    success_count = 0

    for skin_id in range(MAX_SKIN_COUNT):
        skin_url = SKIN_BASE_URL.format(ename=ename, skin_id=skin_id)
        save_path = hero_dir / f"{skin_id}.jpg"

        if download_image(skin_url, save_path, timeout=timeout, retries=retries):
            success_count += 1
        else:
            print(f"  - 皮肤 {skin_id} 不存在或下载失败，停止继续尝试该英雄后续皮肤")
            break

        time.sleep(random.uniform(sleep_min, sleep_max))

    print(f"[完成] {hero_name}：成功下载 {success_count} 张皮肤\n")


def download_all_skins(output_dir: Path, timeout: int = DEFAULT_TIMEOUT, retries: int = MAX_RETRIES,
                       sleep_min: float = 1.0, sleep_max: float = 3.0) -> None:
    """下载所有英雄的皮肤图片

    Args:
        output_dir: 根输出目录
        timeout: 请求超时时间（秒）
        retries: 失败重试次数
        sleep_min: 两次下载之间最小休眠时间（秒）
        sleep_max: 两次下载之间最大休眠时间（秒）
    """
    print(f"输出目录：{output_dir.resolve()}")
    print(f"超时：{timeout}s  重试：{retries}次  休眠：{sleep_min}-{sleep_max}s\n")

    try:
        hero_list = fetch_hero_list(timeout=timeout, retries=retries)
    except RuntimeError as e:
        print(f"[致命错误] {e}")
        return

    print(f"共获取到 {len(hero_list)} 个英雄\n")

    for hero in hero_list:
        try:
            download_hero_skins(
                hero,
                output_dir=output_dir,
                timeout=timeout,
                retries=retries,
                sleep_min=sleep_min,
                sleep_max=sleep_max,
            )
        except KeyboardInterrupt:
            print("\n[中断] 用户取消了下载任务")
            return
        except Exception as e:
            hero_name = hero.get("cname", "未知英雄")
            print(f"[错误] 处理英雄 {hero_name} 时发生异常：{e}")

    print("全部任务执行完毕")


def parse_args() -> argparse.Namespace:
    """解析命令行参数

    Returns:
        解析后的命名空间对象
    """
    default_output = Path.cwd() / "skins"
    parser = argparse.ArgumentParser(
        description="王者荣耀英雄皮肤图片批量下载工具",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=str(default_output),
        help="皮肤图片输出目录",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="网络请求超时时间（秒）",
    )
    parser.add_argument(
        "-r", "--retries",
        type=int,
        default=MAX_RETRIES,
        help="失败重试次数",
    )
    parser.add_argument(
        "--sleep-min",
        type=float,
        default=1.0,
        help="两次下载之间最小休眠时间（秒）",
    )
    parser.add_argument(
        "--sleep-max",
        type=float,
        default=3.0,
        help="两次下载之间最大休眠时间（秒）",
    )
    return parser.parse_args()


def main() -> None:
    """程序主入口"""
    args = parse_args()
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    download_all_skins(
        output_dir=output_dir,
        timeout=args.timeout,
        retries=args.retries,
        sleep_min=args.sleep_min,
        sleep_max=args.sleep_max,
    )


if __name__ == "__main__":
    main()
