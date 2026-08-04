"""
🤖 بات هوش مصنوعی Qwen/Mimo
نسخه حرفه‌ای مشابه Hermes
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
MODEL = "oc/mimo-v2.5-free"  # مدل ثابت - رایگان!

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
    # حذف data: [DONE] از انتهای پاسخ
    if 'data: [DONE]' in raw_text:
        raw_text = raw_text.replace('data: [DONE]', '')
    
    # حذف کاراکترهای اضافی از انتها
    raw_text = raw_text.rstrip()
    
    # تلاش برای تجزیه JSON
    try:
        data = json.loads(raw_text)
        return data
    except json.JSONDecodeError:
        # تلاش برای استخراج JSON از متن
        try:
            # پیدا کردن اولین { و آخرین }
            start = raw_text.find('{')
            end = raw_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = raw_text[start:end]
                data = json.loads(json_str)
                return data
        except:
            pass
    
    return None

# ── دریافت پاسخ از API ──────────────────────────────────────
def get_api_response(user_msg):
    """دریافت پاسخ از API"""
    try:
        # ارسال درخواست به هوش مصنوعی
        response = requests.post(
            f"{API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "تو یک دستیار هوش مصنوعی مفید و صمیمی هستی. به فارسی جواب بده."},
                    {"role": "user", "content": user_msg}
                ],
                "max_tokens": 2000,
                "stream": False
            },
            timeout=60
        )
        
        # تنظیم encoding پاسخ به UTF-8
        response.encoding = 'utf-8'
        
        # بررسی وضعیت پاسخ
        if response.status_code == 200:
            # پاکسازی و تجزیه پاسخ
            data = clean_response(response.text)
            
            if data and "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"پاسخ نامعتبر: {response.text[:500]}")
                return "⚠️ خطا در پردازش پاسخ"
                
        elif response.status_code == 429:
            return "⚠️ درخواست زیاد! لطفاً کمی صبر کنید و دوباره امتحان کنید."
            
        elif response.status_code == 401:
            return "⚠️ خطا: کلید API نامعتبر است!"
            
        elif response.status_code == 402:
            return "⚠️ خطا: اعتبار تمام شده!"
            
        else:
            error_msg = f"⚠️ خطا: {response.status_code}"
            logger.error(f"خطای API: {response.status_code} - {response.text[:200]}")
            return error_msg
            
    except requests.Timeout:
        return "⏰ زمان پاسخ‌دهی تموم شد. دوباره امتحان کن!"
        
    except requests.ConnectionError:
        return "❌ خطا: اتصال به سرور برقرار نشد!"
        
    except Exception as e:
        logger.error(f"خطای غیرمنتظره: {e}")
        return f"⚠️ خطا: {str(e)}"

# ── پیام‌ها ──────────────────────────────────────────────
START_MESSAGE = """
🤖 **سلام! من بات هوش مصنوعی هستم!**

💬 هر سوالی داری بپرس، جواب میدم!

📝 **دستورات:**
/start - شروع
/help - راهنما
/model - نمایش مدل فعلی

⚡ مدل: `mimo-v2.5-free`
💰 هزینه: رایگان!
"""

HELP_MESSAGE = """
📖 **راهنمای بات:**

💬 **نحوه استفاده:**
فقط پیام بفرست، جواب بگیر!

📝 **دستورات:**
/start - شروع مجدد
/help - نمایش این راهنما
/model - نمایش مدل فعلی

🤖 **مدل:** `mimo-v2.5-free`
💰 **هزینه:** رایگان!
"""

MODEL_MESSAGE = f"""
🤖 **مدل فعلی:**
`{MODEL}`

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
    
    # دریافت پاسخ
    bot_reply = get_api_response(user_msg)
    
    # حذف پیام در حال پردازش و ارسال جواب
    await processing.delete()
    await update.message.reply_text(bot_reply)

# ── اجرای بات ──────────────────────────────────────────
def main():
    """اجرای اصلی بات"""
    logger.info("=" * 50)
    logger.info("🤖 بات هوش مصنوعی شروع شد!")
    logger.info(f"🧠 مدل: {MODEL}")
    logger.info(f"🌐 API: {API_URL}")
    logger.info("=" * 50)
    
    # بررسی محیط
    if not check_environment():
        logger.error("❌ متغیرهای محیطی ناقص است. برنامه متوقف می‌شود.")
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
