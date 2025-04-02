import requests
import json
import time
from urllib.parse import unquote

def weibo_hotnews_crawler(url, cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'Cookie': """1111""",
        'X-Requested-With': 'XMLHttpRequest'
    }

    # 解析原始URL参数
    params = {
        'containerid': unquote(url.split('containerid=')[1].split('&')[0]),
        'page_type': 'searchall'
    }

    result = []
    page = 1
    max_results = 10
    print("1 --->")
    while len(result) < max_results:
        api_url = 'https://m.weibo.cn/api/container/getIndex'
        params['page'] = page
        
        try:
            response = requests.get(api_url, headers=headers, params=params)
            print("1 --->")
            if response.status_code != 200:
                print(f'请求失败，状态码：{response.status_code}')
                break

            data = json.loads(response.text)
            print("data\n",data)
            # 解析卡片数据
            for card in data.get('data', {}).get('cards', []):
                # 处理卡片组（card_type=11）
                if card.get('card_type') == 11:
                    for sub_card in card.get('card_group', []):
                        process_card(sub_card, result, max_results)
                else:
                    process_card(card, result, max_results)
                
                if len(result) >= max_results:
                    break

            # 检查是否有下一页
            if data.get('data', {}).get('cardlistInfo', {}).get('page') == page:
                break

            page += 1
            time.sleep(2)

        except Exception as e:
            print(f'发生错误：{str(e)}')
            break

    return result[:max_results]

def process_card(card, result, max_results):
    if card.get('card_type') != 9:
        return
    
    mblog = card.get('mblog')
    if not mblog:
        return
    
    # 处理长文本
    text = mblog.get('text', '')
    if mblog.get('isLongText'):
        long_text = get_long_text(mblog['id'])
        text = long_text if long_text else text

    item = {
        '用户': mblog.get('user', {}).get('screen_name', '未知'),
        '内容': clean_html(text),
        '发布时间': format_weibo_time(mblog.get('created_at')),
        '转发数': mblog.get('reposts_count', 0),
        '评论数': mblog.get('comments_count', 0),
        '点赞数': mblog.get('attitudes_count', 0),
        '来源': mblog.get('source', ''),
        '图片数': mblog.get('pic_num', 0),
        '视频链接': get_video_url(mblog),
        '原文链接': f"https://m.weibo.cn/status/{mblog.get('bid')}"
    }
    
    if len(result) < max_results:
        result.append(item)

def get_long_text(mid):
    try:
        response = requests.get(f'https://m.weibo.cn/statuses/extend?id={mid}')
        data = response.json()
        return data.get('data', {}).get('longTextContent', '')
    except:
        return ''

def clean_html(text):
    from bs4 import BeautifulSoup
    return BeautifulSoup(text, 'html.parser').get_text()

def format_weibo_time(time_str):
    from datetime import datetime
    try:
        return datetime.strptime(time_str, '%a %b %d %H:%M:%S %z %Y').strftime('%Y-%m-%d %H:%M:%S')
    except:
        return time_str

def get_video_url(mblog):
    page_info = mblog.get('page_info', {})
    if page_info.get('type') == 'video':
        return page_info.get('media_info', {}).get('stream_url', '')
    return ''

# 使用示例
cookie = "12344"  # 需要替换真实Cookie
hot_url = "https://m.weibo.cn/search?containerid=100103type%3D1%26t%3D10%26q%3D%2312306%E5%9B%9E%E5%BA%94%E5%AD%95%E5%A6%87%E8%A2%AB%E8%A1%8C%E6%9D%8E%E7%AE%B1%E7%A0%B8%E4%B8%AD%E8%87%B4%E6%97%A9%E4%BA%A7%23&stream_entry_id=31&isnewpage=1&extparam=seat%3D1%26c_type%3D31%26flag%3D2%26pos%3D0%26stream_entry_id%3D31%26dgr%3D0%26band_rank%3D1%26realpos%3D1%26lcate%3D5001%26cate%3D5001%26q%3D%252312306%25E5%259B%259E%25E5%25BA%2594%25E5%25AD%2595%25E5%25A6%2587%25E8%25A2%25AB%25E8%25A1%258C%25E6%259D%258E%25E7%25AE%25B1%25E7%25A0%25B8%25E4%25B8%25AD%25E8%2587%25B4%25E6%2597%25A9%25E4%25BA%25A7%2523%26filter_type%3Drealtimehot%26display_time%3D1739946427%26pre_seqid%3D1739946427029015380977"
data = weibo_hotnews_crawler(hot_url, cookie)

# 保存结果
import pandas as pd
df = pd.DataFrame(data)
df.to_csv('weibo_news.csv', index=False, encoding='utf-8-sig')
print("数据已保存到 weibo_news1.csv")
