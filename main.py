import asyncio
from lib2to3.fixes.fix_input import context

import botpy
import os
import requests
from bs4 import BeautifulSoup
from botpy import BotAPI
from botpy.ext.command_util import Commands
from botpy.manage import GroupManageEvent
from botpy.message import GroupMessage
import time
import sqlite3
from datetime import datetime
import aiohttp
import random
import json

from certifi import contents
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
from selenium.webdriver.support.expected_conditions import element_selection_state_to_be

import r

_log = botpy.logging.get_logger()

session: aiohttp.ClientSession



def upload_file(file_path, remote_path, token):
    upload_url = "https://temp.sitmc.club/admin"
    data = {
        'path': remote_path,
    }
    files = {
        'file': open(file_path, 'rb')
    }
    headers = {
        'Authorization': token
    }


    response = requests.put(upload_url, data=data, files=files, headers=headers)

    return True


async def on_sitmc_backend_error(message: GroupMessage):
    await message.reply(content=f"服务无响应，请稍后再试，若此问题依然存在，请联系机器人管理员")


@Commands("校园天气")
async def query_weather(api: BotAPI, message: GroupMessage, params=None):
    async with aiohttp.ClientSession() as session:
        fx_res, xh_res = await asyncio.gather(
            session.get(f"https://restapi.amap.com/v3/weather/weatherInfo?city=310120&key=" + r.weather_api_token),
            session.get(f"https://restapi.amap.com/v3/weather/weatherInfo?city=310104&key=" + r.weather_api_token)
        )

        if fx_res.ok:
            fx_result = await fx_res.json()
            xh_result = await xh_res.json()
            if fx_result.get("status") == "1" and "lives" in fx_result and len(fx_result["lives"]) > 0:
                fx_live_data = fx_result["lives"][0]
                xh_live_data = xh_result["lives"][0]

                fx_weather = fx_live_data.get("weather", "N/A")
                fx_temperature = fx_live_data.get("temperature", "N/A")
                fx_winddirection = fx_live_data.get("winddirection", "N/A")
                fx_windpower = fx_live_data.get("windpower", "N/A")
                fx_humidity = fx_live_data.get("humidity", "N/A")

                xh_weather = xh_live_data.get("weather", "N/A")
                xh_temperature = xh_live_data.get("temperature", "N/A")
                xh_winddirection = xh_live_data.get("winddirection", "N/A")
                xh_windpower = xh_live_data.get("windpower", "N/A")
                xh_humidity = xh_live_data.get("humidity", "N/A")

                reporttime = fx_live_data.get("reporttime", "N/A")

                reply_content = (
                    f"奉贤校区：\n"
                    f"天气：{fx_weather}\n"
                    f"温度：{fx_temperature}\n"
                    f"风向：{fx_winddirection}\n"
                    f"风力：{fx_windpower}\n"
                    f"湿度：{fx_humidity}\n"
                    f"\n"
                    f"徐汇校区：\n"
                    f"天气：{xh_weather}\n"
                    f"温度：{xh_temperature}\n"
                    f"风向：{xh_winddirection}\n"
                    f"风力：{xh_windpower}\n"
                    f"湿度：{xh_humidity}\n"
                    f"更新时间：{reporttime}"
                )

                await message.reply(content=reply_content)
            else:
                error_content = "查询失败，响应数据不正确"
                await message.reply(content=error_content)
        else:
            error_content = "查询失败，无法连接到天气服务"
            await message.reply(content=error_content)
        return True


@Commands("服务器状态")
async def query_sitmc_server(api: BotAPI, message: GroupMessage, params=None):
    async with session.post(f"https://mc.sjtu.cn/custom/serverlist/?query=play.sitmc.club") as res:
        result = await res.json()
        if res.ok:
            server_info = result
            description = server_info.get('description_raw', {}).get('extra', [{}])[0].get('text', '无描述')
            players_max = server_info.get('players', {}).get('max', '未知')
            players_online = server_info.get('players', {}).get('online', '未知')
            version = server_info.get('version', '未知')

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            random_image = random.choice(["1.jpg", "2.jpg", "3.jpg"])
            image_url = f"https://tietu.mclists.cn/banner/purple/7685/{random_image}"

            uploadmedia = await api.post_group_file(
                group_openid=message.group_openid,
                file_type=1,
                url=image_url
            )

            reply_content = (
                f"\n"
                f"服务器名称: SIT-Minecraft\n"
                f"描述: {description}\n"
                f"在线玩家: {players_online}/{players_max}\n"
                f"版本: {version}\n"
                f"查询时间: {timestamp}"
            )

            await message.reply(
                content=reply_content,
                msg_type=7,
                media=uploadmedia
            )
        else:
            error_content = (
                f"查询SITMC服务器信息失败\n"
                f"状态码: {res.status}\n"
                f"响应内容: {result}"
            )
            await message.reply(content=error_content)
        return True


@Commands("一言")
async def daily_word(api: BotAPI, message: GroupMessage, params=None):
    daily_word = f"https://www.mxnzp.com/api/daily_word/recommend?count=1&app_id={r.api_app_id}&app_secret={r.api_app_secret}"
    async with session.post(daily_word) as res:
        result = await res.json()
        if res.ok:
            content = result['data'][0]['content']

            reply_content = (
                f"\n"
                f"{content}"
            )

            await message.reply(content=reply_content)
        else:
            error_content = (
                f"获取一言失败"
            )
            await message.reply(content=error_content)
        return True


@Commands("今日运势")
async def jrys(api: BotAPI, message: GroupMessage, params=None):
    conn = sqlite3.connect('user_numbers.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_numbers (
            user_id TEXT PRIMARY KEY,
            random_number INTEGER,
            number INTEGER,
            date TEXT
        )
    ''')
    conn.commit()

    with open('jrys.json', 'r', encoding='utf-8') as file:
        jrys_data = json.load(file)

    def get_fortune_number(lucky_star):
        star_count = lucky_star.count('★')
        if star_count == 0:
            return random.randint(0, 10)
        elif star_count == 1:
            return random.randint(5, 15)
        elif star_count == 2:
            return random.randint(10, 25)
        elif star_count == 3:
            return random.randint(25, 40)
        elif star_count == 4:
            return random.randint(40, 55)
        elif star_count == 5:
            return random.randint(55, 70)
        elif star_count == 6:
            return random.randint(70, 85)
        elif star_count == 7:
            return random.randint(85, 100)
        else:
            return None

    def get_user_number(user):
        today_date = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('SELECT random_number, number FROM user_numbers WHERE user_id = ? AND date = ?',
                       (user, today_date))
        row = cursor.fetchone()

        if row:
            random_number = row[0]
            number = row[1]
            fortune_data = jrys_data[str(random_number)][0]
        else:
            while True:
                random_number = random.randint(1, 1433)
                fortune_data = jrys_data.get(str(random_number))

                if fortune_data:
                    fortune_data = fortune_data[0]
                    lucky_star = fortune_data['luckyStar']
                    number = get_fortune_number(lucky_star)

                    if number is not None:
                        break

            cursor.execute('''
                INSERT OR REPLACE INTO user_numbers (user_id, random_number, number, date) 
                VALUES (?, ?, ?, ?)
            ''', (user, random_number, number, today_date))
            conn.commit()

        return random_number, number, fortune_data

    user = f"{message.author.member_openid}"
    random_number, assigned_number, fortune_data = get_user_number(user)

    reply = (
        f"\n"
        f"今日运势：{fortune_data['fortuneSummary']}\n"
        f"幸运星象：{fortune_data['luckyStar']}\n"
        f"运势评述：{fortune_data['signText']}\n"
        f"评述解读：{fortune_data['unSignText']}"
    )

    await message.reply(content=reply)
    return True


@Commands("今日人品")
async def jrrp(api: BotAPI, message: GroupMessage, params=None):
    conn = sqlite3.connect('user_numbers.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_numbers (
            user_id TEXT PRIMARY KEY,
            random_number INTEGER,
            number INTEGER,
            date TEXT
        )
    ''')
    conn.commit()

    with open('jrys.json', 'r', encoding='utf-8') as file:
        jrys_data = json.load(file)

    def get_fortune_number(lucky_star):
        star_count = lucky_star.count('★')
        if star_count == 0:
            return random.randint(0, 10)
        elif star_count == 1:
            return random.randint(5, 15)
        elif star_count == 2:
            return random.randint(10, 25)
        elif star_count == 3:
            return random.randint(25, 40)
        elif star_count == 4:
            return random.randint(40, 55)
        elif star_count == 5:
            return random.randint(55, 70)
        elif star_count == 6:
            return random.randint(70, 85)
        elif star_count == 7:
            return random.randint(85, 100)
        else:
            return None

    def get_user_number(user):
        today_date = datetime.now().strftime('%Y-%m-%d')

        cursor.execute('SELECT random_number, number FROM user_numbers WHERE user_id = ? AND date = ?',
                       (user, today_date))
        row = cursor.fetchone()

        if row:
            random_number = row[0]
            number = row[1]
            fortune_data = jrys_data[str(random_number)][0]
        else:
            while True:
                random_number = random.randint(1, 1433)
                fortune_data = jrys_data.get(str(random_number))

                if fortune_data:
                    fortune_data = fortune_data[0]
                    lucky_star = fortune_data['luckyStar']
                    number = get_fortune_number(lucky_star)

                    if number is not None:
                        break

            cursor.execute('''
                INSERT OR REPLACE INTO user_numbers (user_id, random_number, number, date) 
                VALUES (?, ?, ?, ?)
            ''', (user, random_number, number, today_date))
            conn.commit()

        return number

    user = f"{message.author.member_openid}"
    assigned_number = get_user_number(user)

    reply = f"今日人品值：{assigned_number}"

    await message.reply(content=reply)
    return True


@Commands("十大热帖")
async def forum_hot_discussion(api: BotAPI, message: GroupMessage, params=None, requests=None):
    url = "https://forum.mysit.life/api/discussions?sort=-commentCount&page%5Blimit%5D=10"
    headers = {
        "Authorization": "Token " + r.forum_token
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                titles = [discussion.get('attributes', {}).get('title') for discussion in data.get('data', [])]

                reply_content = "\n".join([f"{i}. {title}" for i, title in enumerate(titles, start=1)])
            else:
                reply_content = f"请求失败，状态码: {response.status}"
            await message.reply(content=reply_content)
    return True

@Commands("mcci")
async def mcci(api: BotAPI, message: GroupMessage, params=None, requests=None):
    params = {"raw": params}
    playername = params["raw"].lower()
    url = "https://stats.sirarchibald.dev/player/" + playername

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        error_message = soup.find("p", class_="text-center text-xl text-neutral-900 dark:text-neutral-100 py-2")


    if error_message and "I couldn't find any data for that player!" in error_message.text:
        await message.reply(content="我在Mccisland找不到这个玩家的数据哦(；′⌒`)")
    else:
        save_path = "temp/mccisland"
        os.makedirs(save_path, exist_ok=True)

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--force-device-scale-factor=1.5")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1300, 1000)
        driver.get(url)
        driver.implicitly_wait(5)

        # 保存完整截图
        full_screenshot = os.path.join(save_path, f"full_{playername}.png")
        driver.save_screenshot(full_screenshot)

        # 裁剪截图
        left, top, right, bottom = 14, 124, 478 + 14, 708 + 124
        image = Image.open(full_screenshot)
        final_screenshot = image.crop((left, top, right, bottom))
        final_screenshot_path = os.path.join(save_path, f"{playername}.png")
        final_screenshot.save(final_screenshot_path)

        driver.quit()

        file_path = save_path + f"/{playername}.png"
        remote_path = f"mccisland/{playername}.png"
        token = r.sitmc_server

        result = upload_file(file_path, remote_path, token)
        print(result)

        image_url = f"https://temp.sitmc.club/download/mccisland/{playername}.png"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        uploadmedia = await api.post_group_file(
            group_openid=message.group_openid,
            file_type=1,
            url=image_url
        )

        await message.reply(
            msg_type=7,
            media=uploadmedia
        )
    return True


handlers = [
    query_weather,
    query_sitmc_server,
    daily_word,
    jrrp,
    jrys,
    forum_hot_discussion,
    mcci,
]


class SitmcClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot[{self.robot.name}] is ready.")

    async def on_group_at_message_create(self, message: GroupMessage):
        for handler in handlers:
            if await handler(api=self.api, message=message):
                return
        await message.reply(content=f"不明白你在说什么哦(๑• . •๑)")

    async def on_group_add_robot(self, message: GroupManageEvent):
        await self.api.post_group_message(group_openid=message.group_openid, content="欢迎使用SIT-Minecraft QQ Bot服务")

    async def on_group_del_robot(self, event: GroupManageEvent):
        _log.info(f"robot[{self.robot.name}] left group ${event.group_openid}")


async def main():
    global session
    session = aiohttp.ClientSession()
    intents = botpy.Intents(
        public_messages=True
    )
    client = SitmcClient(intents=intents, is_sandbox=True, log_level=10, timeout=30)
    await client.start(appid=r.appid, secret=r.secret)
    await session.close()


asyncio.run(main())