"""
🤖 بات هوش مصنوعی Qwen/Mimo
ساده و مشابه Hermes
"""

import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

# ── تنظیمات (ثابت) ──────────────────────────────────────────────
API_KEY = os.environ.get('OPENAI_API_KEY')
API_URL = os.environ.get('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')
MODEL = "oc/mimo-v2.5-free"  # مدل ثابت - رایگان!

# ── پیام شروع ──────────────────────────────────────────
START_MESSAGE = """
🤖 **سلام! من بات هوش مصنوعی هستم!**

💬 هر سوالی داری بپرس، جواب میدم!

📝 **دستورات:**
/start - شروع
/help - راهنما

⚡ مدل: `mimo-v2.5-free`
💰 هزینه: رایگان!
"""

# ── دستور شروع ──────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_MESSAGE, parse_mode='Markdown')

# ── دستور راهنما ──────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 **راهنمای بات:**

💬 **نحوه استفاده:**
فقط پیام بفرست، جواب بگیر!

📝 **دستورات:**
/start - شروع مجدد
/help - نمایش این راهنما

🤖 **مدل:** `mimo-v2.5-free`
💰 **هزینه:** رایگان!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ── چت با هوش مصنوعی ──────────────────────────────────────
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    
    # نمایش در حال پردازش
    processing = await update.message.reply_text("⏳ در حال پردازش...")
    
    try:
        # ارسال درخواست به هوش مصنوعی
        response = requests.post(
            f"{API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": "تو یک دستیار هوش مصنوعی مفید و صمیمی هستی. به فارسی جواب بده."},
                    {"role": "user", "content": user_msg}
                ],
                "max_tokens": 2000
            },
            timeout=60
        )
        
        # بررسی پاسخ
        if response.status_code == 200:
            data = response.json()
            bot_reply = data["choices"][0]["message"]["content"]
            
            # حذف پیام در حال پردازش و ارسال جواب
            await processing.delete()
            await update.message.reply_text(bot_reply)
            
        else:
            error_msg = f"⚠️ خطا: {response.status_code}"
            await processing.edit_text(error_msg)
            
    except requests.Timeout:
        await processing.edit_text("⏰ زمان پاسخ‌دهی تموم شد. دوباره امتحان کن!")
        
    except Exception as e:
        error_msg = f"⚠️ خطا: {str(e)}"
        await processing.edit_text(error_msg)

# ── اجرای بات ──────────────────────────────────────────
def main():
    print("=" * 50)
    print("🤖 بات هوش مصنوعی شروع شد!")
    print(f"🧠 مدل: {MODEL}")
    print(f"🌐 API: {API_URL}")
    print("=" * 50)
    
    # ساخت اپلیکیشن
    app = ApplicationBuilder().token(os.environ['BOT_TOKEN']).build()
    
    # اضافه کردن دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    
    # اضافه کردن هندلر چت
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    # شروع بات
    print("✅ بات آماده دریافت پیام!")
    app.run_polling()

if __name__ == '__main__':
    main()
