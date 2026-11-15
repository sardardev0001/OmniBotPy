# OmniBotPy — کتابخانه ربات‌سازی چندپیام‌رسانی پایتون

[English README](README.md) | **فارسی**

کتابخانه‌ای **ناهم‌گام و توسعه‌پذیر** برای ساخت ربات‌های تلگرام، بله و **سروش‌پلاس (آزمایشی)** با دو روش نوشتن کد: **دکوریتور** و **کلاس‌های OOP**. هر دو روش از یک Dispatcher و Adapterهای مشترک استفاده می‌کنند.

> **شفافیت وضعیت:** این نسخه `0.2.0` یک نسخه بتای اجرایی و تست‌شده با Mock HTTP است، نه پیاده‌سازی ۱۰۰ درصد همه متدهای رسمی پیام‌رسان‌ها. اتصال زنده با توکن واقعی آزمایش نشده و API سروش‌پلاس از منابع شخص ثالث استنباط شده است. جدول دقیق در [وضعیت پیاده‌سازی](docs/STATUS.md) آمده است.

## امکانات

- دریافت رویداد و پردازش پیام با ساختار واحد.
- Handler به روش دکوریتوری، کلاس و Controller.
- ثبت هم‌زمان چند ربات با `MultiBot`.
- API خام `call_method` برای متدهای اختصاصی پلتفرم.
- Long Polling، دریافت Webhook از طریق فریم‌ورک وب خودتان، Middleware.
- تشخیص صریح قابلیت‌ها و خطاهای HTTP/API.
- آپلود واقعی multipart فایل عکس و سند و ساخت دکمه‌های Inline/Reply.
- FSM حافظه‌ای برای مراحل گفتگو و مدیریت وضعیت.
- میانبرهای متدهای ثبت‌شده و مدیریت امن‌تر خطاها.
- ۲۸ تست خودکار بدون نیاز به توکن واقعی.

## نصب روی ویندوز

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pytest -q
```

برای اجرا، به‌جای گذاشتن توکن در فایل‌های Git، متغیر محیطی تعریف کنید:

```powershell
$env:BOT_PLATFORM = 'telegram' # یا bale یا soroush
$env:BOT_TOKEN = 'YOUR_REAL_TOKEN'
.\.venv\Scripts\python.exe examples\decorators.py
```

## نمونه دکوریتوری

```python
import os
from omnibotpy import Bot, Platform

bot = Bot(Platform.TELEGRAM, os.environ["BOT_TOKEN"])

@bot.command("start")
async def start(ctx):
    await ctx.reply("سلام! خوش آمدید")

@bot.message()
async def echo(ctx):
    if ctx.text:
        await ctx.reply(ctx.text)

bot.run()
```

## نمونه OOP

```python
import os
from omnibotpy import Bot, Platform, CommandHandler, MessageHandler

class Start(CommandHandler):
    command = "start"
    async def handle(self, ctx):
        await ctx.reply("سلام از کلاس Start!")

class Echo(MessageHandler):
    async def handle(self, ctx):
        if ctx.text:
            await ctx.reply(ctx.text)

bot = Bot(Platform.BALE, os.environ["BOT_TOKEN"])
bot.add_handler(Start())
bot.add_handler(Echo())
bot.run()
```

## حالت Controller

```python
from omnibotpy import BotController

class MainController(BotController):
    async def on_start(self, ctx):
        await ctx.reply("خوش آمدید")

    async def on_message(self, ctx):
        await ctx.reply("پیام دریافت شد")

bot.add_controller(MainController())
```

## کار با وضعیت و دکمه‌ها

```python
from omnibotpy import InlineButton, InlineKeyboard

@bot.command("start")
async def start(ctx):
    await ctx.set_state("name")
    await ctx.reply("اسمت چیه؟", reply_markup=InlineKeyboard([
        [InlineButton("راهنما", callback_data="help")]
    ]))

@bot.message()
async def name(ctx):
    state = await ctx.get_state()
    if state.state == "name" and ctx.text:
        await ctx.clear_state()
        await ctx.reply(f"خوش آمدی {ctx.text}")
```

برای آپلود فایل محلی از `await bot.adapter.send_document_file(chat_id, "path.pdf")` استفاده کن. فایل فعلاً یک‌جا در حافظه بارگذاری می‌شود؛ برای فایل‌های بزرگ و تولید، نیاز به پیاده‌سازی streaming است. FSM پیش‌فرض هم حافظه‌ای است و بعد از Restart پاک می‌شود.

برای متدهای ثبت‌شده میانبر snake_case نیز وجود دارد، ولی پارامترهای آن‌ها هنوز مدل‌های تایپ‌شده مستقل ندارند؛ API خام `call_method` هم در دسترس است.

## پشتیبانی پیام‌رسان‌ها

| ویژگی | تلگرام | بله | سروش‌پلاس |
| --- | --- | --- | --- |
| HTTP Bot API Wrapper | پایه + API خام | پایه + API خام | آزمایشی |
| دکوریتور و OOP | دارد | دارد | دارد (با فرض رویداد سازگار) |
| دریافت با polling | پیاده‌سازی و تست Mock | پیاده‌سازی و تست Mock | نیازمند تست واقعی |
| Webhook | تنظیم + Dispatcher | تنظیم + Dispatcher | تنظیم مستقیم غیرفعال تا تأیید |
| آپلود مستقیم فایل باینری | پیاده‌سازی Mock | پیاده‌سازی Mock | کد آزمایشی، تست زنده نشده |
| تمام متدهای تایپ‌شده | هنوز ندارد | هنوز ندارد | هنوز ندارد |

**مهم:** `call_method()` به معنی تضمین پشتیبانی همه متدهای یک پیام‌رسان نیست. قبل از استفاده از قابلیت‌های اختصاصی، مستندات هر سرویس و پاسخ API را بررسی کنید.

## منابع API

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [مستندات رسمی بازوی بله](https://docs.bale.ai/)
- [مستندات Plustik برای سروش‌پلاس (غیررسمی)](https://plustik.readthedocs.io/en/latest/api/plustik/client/index.html)

برای شفافیت وضعیت و محدودیت‌ها [STATUS](docs/STATUS.md)، [معماری](docs/ARCHITECTURE.md) و [مشارکت](CONTRIBUTING.md) را بخوانید.

## گیت‌هاب و انتشار

مخزن با `.gitignore`، مجوز MIT، مثال‌ها، تست‌ها و GitHub Actions آماده شده است. **نام پکیج `omnibotpy-sdk` فعلاً پیشنهادی است و آزادبودن نام در PyPI بررسی نشده است.** کلیدها و فایل `.env` را هرگز commit نکنید.

## نقشه راه

پوشش متدهای تایپ‌شده کامل تلگرام و بله، قراردادهای تأییدشده سروش‌پلاس، FSM پایدار، محدودسازی نرخ، ذخیره Offset و تست اتصال واقعی.

جزئیات بیشتر: [وضعیت فنی و محدودیت‌ها](docs/STATUS.md) · [راهنمای امنیت](SECURITY.md) · [تغییرات](CHANGELOG.md) · [مجوز MIT](LICENSE)
