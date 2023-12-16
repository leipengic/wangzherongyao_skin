import os
import requests
import time
import random
from fake_useragent import UserAgent
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_directory(directory_path):
    """
    创建目录，如果目录已存在，则不执行任何操作。
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def download_image(hero_name, hero_number, image_index):
    """
    下载图片到指定文件夹。
    """
    onehero_link = f'http://game.gtimg.cn/images/yxzj/img201606/skin/hero-info/{hero_number}/{hero_number}-bigskin-{image_index}.jpg'
    ua = UserAgent()
    headers = {'User-Agent': ua.random}

    try:
        im = requests.get(onehero_link, headers=headers, timeout=10)
        if im.status_code == 200:
            file_path = os.path.join(hero_name, f'{image_index}.jpg')
            with open(file_path, 'wb') as f:
                f.write(im.content)
            logging.info(f"成功下载图片 {image_index}.jpg")
        else:
            logging.warning(f"下载失败，状态码：{im.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"下载请求出错：{e}")


def download_pic(hero_name, hero_number):
    """
    对每个英雄，下载其皮肤图片。
    """
    for k in range(10):
        download_image(hero_name, hero_number, k)
        time.sleep(random.randint(10, 20))


def main():
    url = 'https://pvp.qq.com/web201605/js/herolist.json'
    try:
        herolist_response = requests.get(url, timeout=10)
        herolist_json = herolist_response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"获取英雄列表失败：{e}")
        return

    skin_root_directory = "D:/Project/test]/skin"
    create_directory(skin_root_directory)

    for i, hero in enumerate(herolist_json):
        hero_name = hero['cname']
        hero_number = hero['ename']
        hero_directory = os.path.join(skin_root_directory, hero_name)
        create_directory(hero_directory)
        download_pic(hero_name, hero_number)
        logging.info(f"已完成 {hero_name} 的皮肤下载")


if __name__ == "__main__":
    main()