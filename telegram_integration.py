import telegram
import asyncio
import html
import re

from telegram.constants import ParseMode

bot_token = ''
group_chat_id = ''

async def send(msg, chat_id, token=bot_token):
    # Create a bot instance
    bot = telegram.Bot(token=bot_token)

    # Send the message to the group
    await bot.send_message(chat_id=group_chat_id, text=msg, parse_mode=ParseMode.HTML)
    print("Message Sent to Telegram...")

##MessageString = 'Testing from virtual server'
##print(MessageString)
#asyncio.run(send(msg=MessageString, chat_id=group_chat_id, token=bot_token))


def replace_angle_brackets(input_string):
    # Escape the entire string except for specific tags
    escaped_string = html.escape(input_string, quote=False)

    # Define tags that should not be escaped
    no_escape_tags = {'b', 'i', 'a', 'code', 'pre'}

    # Replace the escaped tags with their original form
    for tag in no_escape_tags:
        open_tag = f"&lt;{tag}&gt;"
        close_tag = f"&lt;/{tag}&gt;"
        escaped_string = escaped_string.replace(open_tag, f"<{tag}>").replace(close_tag, f"</{tag}>")

    return escaped_string

def send_message_to_telegram(msg):
    msg = replace_angle_brackets(msg)
    asyncio.run(send(msg=msg, chat_id=group_chat_id, token=bot_token))