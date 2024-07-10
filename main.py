import asyncio

import botpy
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

from io import BytesIO
from typing import Optional, Dict, Any, List

from PIL import Image, ImageDraw
from enum import Enum
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

from wordle.data_source import legal_word, random_word, load_font, save_png
from wordle.utils import Wordle, GuessResult

import r

_log = botpy.logging.get_logger()

session: aiohttp.ClientSession


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

@Commands("像素上应")
async def PixelSIT(api: BotAPI, message: GroupMessage, params=None):
    pass

"""
games: Dict[str, Wordle] = {}
timers: Dict[str, asyncio.TimerHandle] = {}


def game_is_running(chat_id: str) -> bool:
    return chat_id in games


def game_not_running(chat_id: str) -> bool:
    return chat_id not in games


def stop_game(chat_id: str):
    if timer := timers.pop(chat_id, None):
        timer.cancel()
    games.pop(chat_id, None)


async def stop_game_timeout(chat_id: str):
    stop_game(chat_id)


def set_timeout(chat_id: str, timeout: float = 300):
    if timer := timers.get(chat_id, None):
        timer.cancel()
    loop = asyncio.get_running_loop()
    timer = loop.call_later(
        timeout, lambda: asyncio.ensure_future(stop_game_timeout(chat_id))
    )
    timers[chat_id] = timer


@Commands("Wordle")
async def start_game(api: BotAPI, message: GroupMessage, params=None):
    params = {"raw": params}
    chat_id = message.group_openid
    if game_is_running(chat_id):
        await message.reply(content=f"游戏已经在进行中")
        return

    args = params["raw"].split()
    length = 5
    dictionary = "CET4"
    if len(args) > 0:
        try:
            length = int(args[0])
            if length < 3 or length > 8:
                await message.reply(content="单词长度应在3~8之间")
                return
        except ValueError:
            await message.reply(content=f"无效的单词长度")
            return

    dic_list=[f"CET-4", f"CET-6"]

    if len(args) > 1:
        dictionary = args[1]
        if dictionary not in dic_list:
            await message.reply(content=f"支持的词典：" + ", ".join(dic_list))
            return

    word, meaning = random_word(dictionary, length)
    game = Wordle(word, meaning)

    games[chat_id] = game
    set_timeout(chat_id)

    image_url = f""

    uploadmedia = await api.post_group_file(
        group_openid=message.group_openid,
        file_type=1,
        url=image_url
    )

    msg = f"你有{game.rows}次机会猜出单词，单词长度为{game.length}，请发送单词"
    await message.reply(
        content=msg,
        msg_type=7,
        media=uploadmedia
    )


# 提示指令处理
async def give_hint(message: types.Message):
    chat_id = message.chat.id
    if game_not_running(chat_id):
        await message.reply("当前没有正在进行的游戏。")
        return

    game = games[chat_id]
    set_timeout(chat_id)

    hint = game.get_hint()
    if not hint.replace("*", ""):
        await message.reply("你还没有猜对过一个字母哦~再猜猜吧~")
        return

    await bot.send_photo(chat_id, InputFile(game.draw_hint(hint)))


async def stop_current_game(message: types.Message):
    chat_id = message.chat.id
    if game_not_running(chat_id):
        await message.reply("当前没有正在进行的游戏。")
        return

    game = games[chat_id]
    stop_game(chat_id)

    msg = "游戏已结束"
    if len(game.guessed_words) >= 1:
        msg += f"\n{game.result}"
    await message.reply(msg)


# 单词猜测处理
async def handle_guess(message: types.Message):
    chat_id = message.chat.id
    game = games[chat_id]
    set_timeout(chat_id)

    word = message.text.lower()
    result = game.guess(word)

    if result == GuessResult.WIN:
        stop_game(chat_id)
        msg = f"恭喜你猜出了单词！\n{game.result}"
        await message.reply(msg)
        await bot.send_photo(chat_id, InputFile(game.draw()))
    elif result == GuessResult.LOSS:
        stop_game(chat_id)
        msg = f"很遗憾，没有人猜出来呢\n{game.result}"
        await message.reply(msg)
        await bot.send_photo(chat_id, InputFile(game.draw()))
    elif result == GuessResult.DUPLICATE:
        await message.reply("你已经猜过这个单词了呢")
    elif result == GuessResult.ILLEGAL:
        await message.reply(f"你确定 {word} 是一个合法的单词吗？")
    else:
        await bot.send_photo(chat_id, InputFile(game.draw()))

    return True

"""


handlers = [
    query_weather,
    query_sitmc_server,
    daily_word,
    jrrp,
    jrys
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
