# 🚀 ماسح إشارات العملات المشفرة

<div dir="rtl">

## نظرة عامة

هذا المشروع هو ماسح آلي لإشارات العملات المشفرة يعمل على مدار الساعة. يقوم بتحليل جميع أزواج USDT على منصة Binance باستخدام التحليل الفني على الإطار الزمني每小时 (1H) ويعرض الإشارات المكتشفة على لوحة تحكم عربية احترافية.

## ✨ المميزات

- 🔍 **فحص شامل**: يحلل حتى 200 زوج USDT نشط (حجم > 1,000,000 USDT)
- 📊 **3 استراتيجيات فنية**: استمرار الاتجاه، تقاطع الزخم، انعكاس MACD
- 🌐 **واجهة عربية**: لوحة تحكم RTL بالكامل باللغة العربية
- ⏰ **تحديث تلقائي**: يعمل كل ساعة تلقائياً عبر GitHub Actions
- 📱 **تصميم متجاوب**: يعمل على جميع الأجهزة
- 🎨 **تصميم احترافي**: الوضع الداكن مع تأثيرات متحركة

## 📈 الاستراتيجيات الفنية

### الاستراتيجية A - استمرار الاتجاه الصاعد 📈
- السعر فوق EMA 200 (الاتجاه العام صاعد)
- SuperTrend bullish (اتجاه صاعد)
- RSI بين 45 و 65 (منطقة القوة المتوازنة)

### الاستراتيجية B - تقاطع الزخم الصاعد ⚡
- EMA 20 يعبر فوق EMA 50 (تقاطع صاعد)
- الحجم أكبر من 1.5x من متوسط الحجم

### الاستراتيجية C - انعكاس MACD الصاعد 🔄
- خط MACD يعبر فوق خط الإشارة
- السعر فوق EMA 50

## 🛠️ التقنيات المستخدمة

### Backend (Python)
- **requests** - للتعامل مع Binance API
- **pandas** - لمعالجة البيانات (اختياري)
- حساب المؤشرات الفنية يدوياً (EMA, RSI, SuperTrend, MACD)

### Frontend
- **HTML5** - بنية الصفحة
- **Tailwind CSS** - التنسيق (CDN)
- **Vanilla JavaScript** - المنطق
- **Google Fonts (Cairo)** - الخط العربي

## 📁 هيكل الملفات

```
├── scanner.py              # سكربت Python للمسح الفني
├── index.html              # واجهة الويب (لوحة التحكم)
├── signals.json            # ملف بيانات الإشارات (يتحدث تلقائياً)
├── requirements.txt        # حزم Python المطلوبة
├── README.md               # هذا الملف
└── .github/
    └── workflows/
        └── scanner.yml     # workflow GitHub Actions
```

## 🔧 الإعداد

### 1. إنشاء مستودع جديد على GitHub

```bash
# إنشاء مستودع جديد
gh repo create crypto-signal-scanner --public --clone
```

### 2. رفع الملفات

```bash
cd crypto-signal-scanner
git add .
git commit -m "Initial commit: Crypto Signal Scanner"
git push origin main
```

### 3. تفعيل GitHub Pages

1. اذهب إلى **Settings** > **Pages**
2. في قسم **Build and deployment**:
   - **Source**: اختر **GitHub Actions**
3. احفظ الإعدادات

### 4. تشغيل المسح يدوياً

1. اذهب إلى تبويب **Actions** في المستودع
2. اختر workflow **ماسح الإشارات**
3. اضغط **Run workflow**

## ⚙️ التخصيص

### تعديل حد الحجم الأدنى
في ملف `scanner.py`، عدّل:
```python
MIN_VOLUME_USDT = 2_000_000  # تغيير من 1M إلى 2M
```

### تعديل عدد الأزواج المعالجة
```python
MAX_PAIRS = 100  # تغيير عدد الأزواج
```

### تعديل إعدادات المؤشرات
في قسم `INDICATOR_CONFIG`:
```python
INDICATOR_CONFIG = {
    "ema_short": 20,      # فترة EMA القصيرة
    "ema_medium": 50,     # فترة EMA المتوسطة
    "ema_long": 200,      # فترة EMA الطويلة
    "rsi_period": 14,     # فترة RSI
    "st_atr": 10,         # فترة ATR لـ SuperTrend
    "st_multiplier": 3,   # مضاعف SuperTrend
    ...
}
```

## 🔄 آلية العمل

```
┌─────────────────────────────────────────────────────┐
│                    كل ساعة (على الساعة 5 دقائق)     │
│                                                     │
│  ┌───────────────┐                                  │
│  │ GitHub Actions │                                  │
│  └───────┬───────┘                                  │
│          │                                           │
│          ▼                                           │
│  ┌───────────────────┐                               │
│  │  scanner.py       │                               │
│  │  - Binance API    │                               │
│  │  - Technical      │                               │
│  │    Analysis       │                               │
│  │  - Signal Gen     │                               │
│  └───────┬───────────┘                               │
│          │                                           │
│          ▼                                           │
│  ┌───────────────────┐                               │
│  │  signals.json     │ ←─── Commit + Push            │
│  └───────┬───────────┘                               │
│          │                                           │
│          ▼                                           │
│  ┌───────────────────┐                               │
│  │  GitHub Pages     │                               │
│  │  index.html       │ ←─── يقرأ signals.json        │
│  └───────────────────┘                               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## ⚠️ إخلاء المسؤولية

هذه الأداة للأغراض التعليمية والمعلوماتية فقط. **ليست نصيحة مالية**. التداول في العملات المشفرة ينطوي على مخاطر عالية. قم بإجراء بحثك الخاص قبل اتخاذ أي قرارات استثمارية.

## 📄 الترخيص

MIT License - استخدم بحرية!

</div>

---

# 🚀 Crypto Signal Scanner

**English:** An automated cryptocurrency signal scanner that analyzes USDT pairs on Binance using technical analysis. Features 3 built-in strategies, Arabic RTL interface, and hourly auto-updates via GitHub Actions.
