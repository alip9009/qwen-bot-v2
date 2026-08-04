"""
🤖 بات هوش مصنوعی MiMo - نسخه کدنویسی
قابلیت کدنویسی + چت عادی
"""

import os
import json
import re
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# ── تنظیمات لاگ ──────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── تنظیمات (ثابت) ──────────────────────────────────────────────
API_KEY = os.environ.get('OPENAI_API_KEY')
API_URL = os.environ.get('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')
MODEL = "oc/mimo-v2.5-free"  # مدل اصلی - رایگان!
CODE_MODEL = "poolside/laguna-xs-2.1:free"  # مدل کدنویسی - رایگان!

# ── بررسی متغیرها ──────────────────────────────────────────
def check_environment():
    """بررسی متغیرهای محیطی مورد نیاز"""
    required = ['BOT_TOKEN', 'OPENAI_API_KEY']
    missing = [var for var in required if not os.environ.get(var)]
    
    if missing:
        logger.error(f"❌ متغیرهای محیطی کمبود: {missing}")
        return False
    
    logger.info("✅ متغیرهای محیطی بررسی شد")
    return True

# ── پاکسازی پاسخ ──────────────────────────────────────────
def clean_response(raw_text):
    """پاکسازی پاسخ از کاراکترهای اضافی"""
    if 'data: [DONE]' in raw_text:
        raw_text = raw_text.replace('data: [DONE]', '')
    
    raw_text = raw_text.rstrip()
    
    try:
        data = json.loads(raw_text)
        return data
    except json.JSONDecodeError:
        try:
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = raw_text[start:end]
                data = json.loads(json_str)
                return data
        except:
            pass
    
    return None

# ── تشخیص کدنویسی ──────────────────────────────────────────
def is_code_request(user_msg):
    """تشخیص اینکه آیا درخواست کدنویسی هست یا نه"""
    code_keywords = [
        'کد', 'بنویس', 'کدنویسی', 'برنامه', 'python', 'javascript', 'java',
        'code', 'write', 'program', 'function', 'api', ' bot', 'ساخت',
        'error', 'خطا', 'باگ', 'bug', 'fix', 'اصلاح', 'تست', 'test',
        'html', 'css', 'react', 'node', 'django', 'flask',
        'کد بزن', 'کد بنویس', 'برنامه بنویس', 'سورس کد', 'source code'
    ]
    
    user_msg_lower = user_msg.lower()
    for keyword in code_keywords:
        if keyword in user_msg_lower:
            return True
    
    # تشخیص کد در متن
    if '```' in user_msg or 'def ' in user_msg or 'import ' in user_msg:
        return True
    
    return False

# ── دریافت پاسخ از API ──────────────────────────────────────
def get_api_response(user_msg, is_code=False):
    """دریافت پاسخ از API"""
    # انتخاب مدل بر اساس نوع درخواست
    model = CODE_MODEL if is_code else MODEL
    
    # System prompt مناسب
    if is_code:
        system_prompt = """تو یک دستیار کدنویسی حرفه‌ای هستی.

قوانین:
1. کدها رو با فرمت مناسب بنویس (```python, ```javascript, etc)
2. توضیحات فارسی بده
3. کدها رو تست شده و آماده اجرا بنویس
4. اگه خطا دیدی، اصلاحش کن
5. از کتابخانه‌های استاندارد استفاده کن

به فارسی جواب بده."""
    else:
        system_prompt = """تو یک دستیار هوش مصنوعی به نام MiMo (میمو) هستی.

مهم: این واقعیت‌ها رو همیشه رعایت کن:
1. نام تو MiMo (میمو) هست
2. تو توسط تیم هوش مصنوعی شیائومی (Xiaomi) ساخته شدی
3. هیچوقت نگو که Claude، GPT، Gemini یا هر مدل دیگه‌ای هستی
4. هیچوقت نگو که توسط Anthropic، OpenAI یا Google ساخته شدی

به فارسی جواب بده. صمیمی و مفید باش."""
    
    try:
        response = requests.post(
            f"{API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg}
                ],
                "max_tokens": 2000,
                "stream": False
            },
            timeout=60
        )
        
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            data = clean_response(response.text)
            
            if data and "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"پاسخ نامعتبر: {response.text[:500]}")
                return "⚠️ خطا در پردازش پاسخ"
                
        elif response.status_code == 429:
            return "⚠️ درخواست زیاد! لطفاً کمی صبر کنید."
            
        elif response.status_code == 401:
            return "⚠️ خطا: کلید API نامعتبر است!"
            
        elif response.status_code == 402:
            return "⚠️ خطا: اعتبار تمام شده!"
            
        else:
            return f"⚠️ خطا: {response.status_code}"
            
    except requests.Timeout:
        return "⏰ زمان پاسخ‌دهی تموم شد."
        
    except requests.ConnectionError:
        return "❌ خطا: اتصال به سرور برقرار نشد!"
        
    except Exception as e:
        logger.error(f"خطای غیرمنتظره: {e}")
        return f"⚠️ خطا: {str(e)}"

# ── پیام‌ها ──────────────────────────────────────────────
START_MESSAGE = """
🤖 **سلام! من بات هوش مصنوعی MiMo هستم!**

💬 هر سوالی داری بپرس، جواب میدم!

📝 **دستورات:**
/start - شروع
/help - راهنما
/model - نمایش مدل فعلی

🧠 مدل: `MiMo-v2.5-free` (شیائومی)
💰 هزینه: رایگان!

💡 **قابلیت‌ها:**
• چت عادی
• کدنویسی
• ترجمه
• و خیلی چیزهای دیگه!
"""

HELP_MESSAGE = """
📖 **راهنمای بات:**

💬 **نحوه استفاده:**
فقط پیام بفرست، جواب بگیر!

📝 **دستورات:**
/start - شروع مجدد
/help - نمایش این راهنما
/model - نمایش مدل فعلی

🧠 **مدل:** `MiMo-v2.5-free` (شیائومی)
💰 **هزینه:** رایگان!

💡 **قابلیت‌ها:**
• چت عادی
• کدنویسی (Python, JavaScript, etc)
• ترجمه
• توضیح مفاهیم
"""

MODEL_MESSAGE = f"""
🧠 **مدل‌های فعلی:**

💬 **چت:** `{MODEL}`
🏢 **سازنده:** شیائومی (Xiaomi)

💻 **کدنویسی:** `{CODE_MODEL}`
🏢 **سازنده:** Poolside

💰 **هزینه:** رایگان!
"""

# ── دستورات ──────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    await update.message.reply_text(START_MESSAGE, parse_mode='Markdown')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور راهنما"""
    await update.message.reply_text(HELP_MESSAGE, parse_mode='Markdown')

async def model_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور نمایش مدل"""
    await update.message.reply_text(MODEL_MESSAGE, parse_mode='Markdown')

# ── چت با هوش مصنوعی ──────────────────────────────────────
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """چت با هوش مصنوعی"""
    user_msg = update.message.text
    
    # نمایش در حال پردازش
    processing = await update.message.reply_text("⏳ در حال پردازش...")
    
    # تشخیص نوع درخواست
    is_code = is_code_request(user_msg)
    
    # دریافت پاسخ
    bot_reply = get_api_response(user_msg, is_code)
    
    # حذف پیام در حال پردازش و ارسال جواب
    await processing.delete()
    await update.message.reply_text(bot_reply)

# ── اجرای بات ──────────────────────────────────────────
def main():
    """اجرای اصلی بات"""
    logger.info("=" * 50)
    logger.info("🤖 بات هوش مصنوعی MiMo شروع شد!")
    logger.info(f"💬 مدل چت: {MODEL}")
    logger.info(f"💻 مدل کد: {CODE_MODEL}")
    logger.info(f"🌐 API: {API_URL}")
    logger.info("=" * 50)
    
    # بررسی محیط
    if not check_environment():
        logger.error("❌ متغیرهای محیطی ناقص است.")
        return
    
    # ساخت اپلیکیشن
    app = ApplicationBuilder().token(os.environ['BOT_TOKEN']).build()
    
    # اضافه کردن دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("model", model_cmd))
    
    # اضافه کردن هندلر چت
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # شروع بات
    logger.info("✅ بات آماده دریافت پیام!")
    app.run_polling()

if __name__ == '__main__':
    main()
