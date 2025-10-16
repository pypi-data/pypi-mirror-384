# Rubigram
A lightweight Python library to build Rubika bots easily.

<div align="center">
  <img src="http://rubigram.ir/rubigram.jpg" alt="Rubigram Logo" width="200"/>
</div>



## Installation
```bash
pip install RubigramClient
```

## Quick Example
```python
from rubigram import Client

bot = Client(token="YOUR_TOKEN")

@bot.on_message()
async def handler(client, message):
    await message.reply("Hello Rubigram!")

bot.run()
```

## Reply and Edit message
```python
from rubigram import Client, filters
from rubigram.types import Update

bot = Client(token="YOUR_TOKEN_BOT")

@bot.on_message(filters.private)
async def echo(client, message: Update):
    send = await message.reply(f"Hi, {message.new_message.text}")
    await send.edit_text("message was edited")

bot.run()
```

## Send Message & Get receiveInlineMessage
```python
from rubigram import Client, filters
from rubigram.types import Update, Button, Keypad, KeypadRow, InlineMessage


bot = Client(token="BOT_TOKEN", endpoint="ENDPOINT_URL")


@bot.on_message(filters.command("start"))
async def start(_, message: Update):
    inline = Keypad(
        rows=[
            KeypadRow(
                buttons=[
                    Button("1", "Button 1"),
                    Button("2", "Button 2")
                ]
            )
        ]
    )
    await bot.send_message(message.chat_id, "Hi", inline_keypad=inline)
    

@bot.on_inline_message(filters.button(["1", "2"]))
async def button(_, message: InlineMessage):
    if message.aux_data.button_id == "1":
        await bot.send_message(message.chat_id, "You Click Button 1")
    elif message.aux_data.button_id == "2":
        await bot.send_message(message.chat_id, "You Click Button 2")
        
bot.run()
```

## Contex Manager
```python
from rubigram import Client
import asyncio

bot = Client("YOUR_BOT_TOKEN")

async def main():
    async with bot:
        data = await bot.get_me()
        print(data.bot_id)

asyncio.run(main())
```

## Implementation of multiple programs
```python
from rubigram import Client
import asyncio

tokens = [
    "TOKEN_1",
    "TOKEN_2"
]

async def main():
    for token in tokens:
        async with Client(token) as bot:
            get_me = await bot.get_me()
            print(get_me.asjson())

asyncio.run(main())
```

## Rubino
```python
from rubigram.rubino import Rubino
import asyncio

async def main():
    auth = "YOUR_AUTH_ACCOUNT"
    async with Rubino(auth) as app:
        info = await app.get_my_profile_info()
        print(info)
        
asyncio.run(main())
```