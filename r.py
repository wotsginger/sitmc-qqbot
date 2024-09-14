import os
from dotenv import load_dotenv

load_dotenv()

appid = os.getenv("QQBOT_APP_ID")
if appid is None:
    raise Exception('Missing "QQBOT_APP_ID" environment variable for your bot AppID')

secret = os.getenv("QQBOT_APP_SECRET")
if secret is None:
    raise Exception('Missing "QQBOT_APP_SECRET" environment variable for your AppSecret')

weather_api_token = os.getenv("WEATHER_API_TOKEN")
if weather_api_token is None:
    raise Exception('Missing "WEATHER_API_TOKEN" environment variable for your AppSecret')

api_app_id = os.getenv("API_APP_ID")
if weather_api_token is None:
    raise Exception('Missing "API_APP_ID" environment variable for your AppSecret')

api_app_secret = os.getenv("API_APP_SECRET")
if weather_api_token is None:
    raise Exception('Missing "API_APP_SECRET" environment variable for your AppSecret')

forum_token = os.getenv("FORUM_TOKEN")
if forum_token is None:
    raise Exception('Missing "FORUM_TOKEN" environment variable for your AppSecret')