# 🤖 بات هوش مصنوعی Qwen/Mimo

## 🚀 راه‌اندازی سریع (مثل Hermes!)

### مرحله ۱: فایل‌ها رو دانلود کن
فایل ZIP رو دانلود و از حالت فشرده خارج کن

### مرحله ۲: GitHub Repo بساز
1. [github.com/new](https://github.com/new) بر
2. نام: `qwen-bot`
3. فایل‌ها رو آپلود کن:
   - `bot.py`
   - `requirements.txt`
   - `Dockerfile`
   - `railway.toml`

### مرحله ۳: Railway Deploy
1. [railway.app](https://railway.app) بر
2. **New Project** → **Deploy from GitHub Repo**
3. ریپو `qwen-bot` رو انتخاب کن

### مرحله ۴: Variables تنظیم کن
فقط این دو رو تنظیم کن:

```
BOT_TOKEN=توکن_بات
OPENAI_API_KEY=sk-39d...ba6b
OPENAI_BASE_URL=https://9router-production-ec58.up.railway.app/v1
```

### مرحله ۵: Deploy!
Railway خودکار deploy میکنه!

---

## 📝 نکته مهم

**مدل رو نیازی نیست تنظیم کنی!** 
مدل `mimo-v2.5-free` در کد ثابت شده و رایگانه!

---

## ✅ تمام!

حالا برو به تلگرام و با باتت چت کن! 🎉
