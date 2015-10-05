import requests
import json
import schedule
import time
import random
import gc

# ------ web crawling term ------
import urllib
num_sticky = 2          # Default stickies in PTT beauty
min_likes = 20          # Posts' "likes" must be larger than this

# ------ Webhook term ------
# All info you can find in your slack team on https://api.slack.com/incoming-webhooks
# Default seed is PTT Beauty
seed = "https://www.ptt.cc/bbs/Beauty/index.html"
web_hook_url = "YOUR_WEB_HOOK_URL"
bot_name = "YOUR_BOT_NAME"
channel_name = "#YOUR-CHANNEL-NAME"
icon = ":monkey_face:"  # Change icon whichever you want

found_url = []

def get_page(url):
    try:
        f = urllib.urlopen(url)
        content = f.read()
        f.close()
        return content
    except:
        return ""
    return ""

def find_likes(content):
    like_find = content.find('</span></div>')
    if like_find == -1:
        return 0, None, None

    start_like_quote = content.find('>', like_find-5)
    end_like_quote = content.find('<', start_like_quote+1)    
    
    try:
        if content[start_like_quote+1:end_like_quote] == "爆":
            num_likes = 100
        else:
            num_likes = int(content[start_like_quote+1:end_like_quote])
    except:
        num_likes = 0

    start_url_find = content.find('<a href=', end_like_quote+1)
    start_url_quote = content.find('"', start_url_find)
    end_url_quote = content.find('"', start_url_quote+1)
    url = "https://www.ptt.cc/" + content[start_url_quote+1: end_url_quote]

    return num_likes, url, end_url_quote

def find_all_likes(content, num_sticky):
    like_with_url = []
    while True:
        results = find_likes(content)
        if results[1]:
            like_with_url.append([results[0], results[1]])
            content = content[results[2]:]
        else:
            break
    
    return like_with_url

def prev_page(content):
    prev_url_find = content.find('">&lsaquo')
    if prev_url_find == -1:
        return None, 0

    start_quote = content.find('"', prev_url_find-30)
    end_quote = content.find('"', start_quote+1)
    prev_url = "https://www.ptt.cc/" + content[start_quote+1: end_quote]

    return prev_url

def check_jpg(image_url):
    if image_url.find('.html') != -1:
        return False
    elif image_url.find('.jpg') == -1 and image_url.find('.JPG') and image_url.find('.PNG') and image_url.find('.png'):
        return image_url + '.jpg'

def find_pictures(content):
    title_find = content.find('<title>')
    title_start_quote = content.find('>', title_find)
    title_end_quote = content.find('-', title_start_quote+1)

    title = content[title_start_quote+1: title_end_quote] + "  "

    image_find = content.find('<a href=')
    image_url_start = content.find('"', image_find)
    image_url_end = content.find('"', image_url_start+1)

    image_url = content[image_url_start+1: image_url_end]

    image_url = check_jpg(image_url)

    return title, image_url

def crawl_beauty(seed, num_sticky, min_likes):
    content = get_page(seed)
    like_with_url = find_all_likes(content, num_sticky)
    
    # Remove default stickies at first page
    for i in range(num_sticky):
        like_with_url.pop()

    most_num_like = 0
    url_to_find = ''

    while True:
        for i in like_with_url:
            if i[0] > most_num_like and i[1] not in found_url and find_pictures(get_page(i[1]))[1]:
                most_num_like = i[0]
                url_to_find = i[1]
        if most_num_like < min_likes:
            content = get_page(prev_page(content))
            like_with_url = find_all_likes(content, num_sticky)
        else:
            break

    found_url.append(url_to_find)
    title, image_url = find_pictures(get_page(url_to_find))

    return title, image_url


def run_bot():
    title, image_url = crawl_beauty(seed, num_sticky, min_likes)
    text_str = [title]
    str_data = {"channel": channel_name, "username": bot_name, "text": text_str[random.randint(0,len(text_str)-1)]+image_url, "icon_emoji": icon}
    requests.post(web_hook_url, data = json.dumps(str_data)).close()

    print title, image_url


# How often should bot crawl
# (default run in 5 hours)
schedule.every(5).hours.do(run_bot)


while True:
    schedule.run_pending()
    time.sleep(1)
    gc.collect()