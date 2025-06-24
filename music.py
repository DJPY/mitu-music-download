import requests
import os
import sys
from mutagen.id3 import ID3, APIC, TIT2, TALB, TPE1, USLT
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, TDRC, TCON, COMM

# 替换为实际的音乐搜索接口
MUSIC_SEARCH_API = "https://www.qqmp3.vip/api/songs.php?type=search"
MUSIC_DOWNLOAD_API = "https://www.qqmp3.vip/api/kw.php?rid={{rid}}&type=json&level=exhigh&lrc=true"

# 模拟浏览器的请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# 创建 music 文件夹
MUSIC_FOLDER = "music"
if not os.path.exists(MUSIC_FOLDER):
    os.makedirs(MUSIC_FOLDER)


def search_music(query):
    try:
        response = requests.get(MUSIC_SEARCH_API,headers=HEADERS, params={"keyword": query})
        response.raise_for_status()
        results = response.json()
        return results
    except requests.RequestException as e:
        print(f"请求接口失败：{e}")
        sys.exit(1)
def get_music_details(rid):
    try:
        url = MUSIC_DOWNLOAD_API.replace("{{rid}}", str(rid))
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        details = response.json()
        return details
    except requests.RequestException as e:
        print(f"请求接口失败：{e}")
        sys.exit(1)

def show_results(results):
    print("查询结果：")
    for index, result in enumerate(results, start=1):
        print(f"{index:03}. {result['artist']} - {result['name']}")

def download_data(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"下载失败：{e}")
        return None

def download_file(url, filename):
    try:
        response = requests.get(url, headers=HEADERS, stream=True)
        response.raise_for_status()
        print(f"正在下载：{filename}")
        file_path = os.path.join(MUSIC_FOLDER, f"{filename}")
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"下载完成")
        return file_path
    except requests.RequestException as e:
        print(f"下载失败：{e}")
        return None

def download_song(download_song):
    filename = download_song['filename']
    title = download_song['title']
    artist = download_song['artist']
    url = download_song['url']
    pic = download_song['pic']
    lrc = download_song['lrc']
    file_path = download_file(url, f"{filename}.mp3")
    if not file_path:
        print("下载歌曲失败")
        return
    # print(f"歌曲已下载：{file_path}")
    image_data = download_data(pic) if pic else None
    if image_data is None:
        print("下载封面图片失败")
        image_data = b''
    else:
        print("封面图片已下载")
    # 下载歌词
    if lrc is None:
        lrc = ''
    if lrc == '暂无歌词':
        lrc = ''
    if not lrc:
        print("未找到歌词")
    else:
        print("歌词已下载")
    # 写入元数据
    print("正在写入元数据...")
    write_metadata(file_path, title, artist, lrc, image_data)

def write_metadata(file_path, title, artist, lyrics, image_data):
    try:
        tags = ID3(file_path)
    except:
        tags = ID3()

    tags.add(TIT2(encoding=3, text=title))  # 歌曲标题
    # tags.add(TALB(encoding=3, text=album))  # 专辑
    tags.add(TPE1(encoding=3, text=artist))  # 主要艺术家
    tags.add(TPE2(encoding=3, text=artist))  # 专辑艺术家
    # tags.add(TDRC(encoding=3, text=year))  # 年份
    # tags.add(TCON(encoding=3, text=genre))  # 音乐类型
    # tags.add(COMM(encoding=3, lang='eng', desc='desc', text=comment))  # 评论
    tags.add(USLT(encoding=3, lang='eng', desc='', text=lyrics))  # 歌词
    tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=image_data))  # 封面图片

    tags.save(file_path)
    print(f"元数据已写入：{file_path}")
    print(f"{artist}-{title} 歌曲下载并处理完成！")


def main():
    query = input("请输入歌曲或艺术家名称：")
    results = search_music(query)
    if not results:
        print("未找到相关结果")
        return
    # print("results:", results)
    if results.get('code') != 200:
        print("查询失败，请稍后再试")
        return
    if not results.get('data'):
        print("未找到相关结果")
        return
    results = results['data']

    show_results(results)
    choices = input("请输入要下载的歌曲编号（可输入多个编号，用空格分隔，输入q退出）：")
    if choices.lower() == 'q':
        print("退出程序")
        return

    try:
        choice_list = [int(c) for c in choices.strip().split() if c.isdigit()]
        if not choice_list:
            print("请输入有效的数字编号")
            return
        for choice in choice_list:
            if 1 <= choice <= len(results):
                selected_song = results[choice - 1]
                resp = get_music_details(selected_song['rid'])
                if resp.get('code') != 200:
                    print(f"获取歌曲详情失败（编号{choice}），请稍后再试")
                    continue
                if not resp.get('data'):
                    print(f"未找到歌曲详情（编号{choice}）")
                    continue
                selected_song = resp['data']
                selected_song['filename'] = f"{selected_song['artist']} - {selected_song['name']}"
                selected_song['title'] = selected_song['name']
                selected_song['artist'] = selected_song['artist']
                download_song(selected_song)
            else:
                print(f"无效的选项：{choice}")
    except ValueError:
        print("请输入有效的数字编号")

if __name__ == "__main__":
    main()
