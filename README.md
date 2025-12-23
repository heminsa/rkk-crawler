
# 📰 Crawler روزنامه رسمی ایران (rrk.ir)

این پروژه یک **Crawler حرفه‌ای و چندنخی (Multi-threaded)** برای استخراج آگهی‌های منتشرشده در **روزنامه رسمی ایران (rrk.ir)** است که با استفاده از **Python و Selenium** توسعه داده شده است.

هدف اصلی این پروژه، نمایش توانایی طراحی یک کرولر پایدار، قابل توسعه و مناسب محیط‌های واقعی (Production-like) برای **تست استخدامی** است.

---

## 🎯 ویژگی‌های اصلی

* ✅ استخراج آگهی‌های روزنامه رسمی از وب‌سایت **rrk.ir**
* 🧵 پردازش **موازی** با استفاده از `ThreadPoolExecutor`
* 📅 کرول آگهی‌ها به تفکیک **تاریخ انتشار**
* 🤖 استفاده از **Selenium (Headless Chrome)** برای عبور از محدودیت‌های JS
* 🪵 سیستم **Logging کامل** (فایل + کنسول)
* 📊 خروجی ساخت‌یافته در قالب **CSV**
* 🧪 مناسب برای دیباگ (ذخیره HTML صفحات)
* ⚙️ طراحی ماژولار و قابل توسعه

---

## 🏗️ ساختار پروژه

<pre class="overflow-visible! px-0!" data-start="972" data-end="1384"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="@w-xl/main:top-9 sticky top-[calc(--spacing(9)+var(--header-height))]"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-text"><span><span>rkk-crawler/
│
├── rkk_crawler/
│   ├── __init__.py
│   └── crawler.py        # منطق اصلی کرولر
│
├── scripts/
│   └── run.py            # نقطه شروع اجرا
│
├── logs/
│   └── rrk_crawler.log   # لاگ‌های اجرای برنامه
│
├── data/
│   └── page_*.html       # HTML صفحات ذخیره‌شده برای دیباگ
│
├── output/
│   └── rrk_ads_*.csv     # خروجی نهایی داده‌ها
│
├── requirements.txt
├── .gitignore
└── README.md
</span></span></code></div></div></pre>

---

## ⚙️ پیش‌نیازها

* Python **3.9+**
* Google Chrome
* ChromeDriver (هماهنگ با نسخه Chrome)

---

## 📦 نصب وابستگی‌ها

پیشنهاد می‌شود از محیط مجازی استفاده کنید:

<pre class="overflow-visible! px-0!" data-start="1554" data-end="1612"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="@w-xl/main:top-9 sticky top-[calc(--spacing(9)+var(--header-height))]"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>python -m venv .venv
</span><span>source</span><span> .venv/bin/activate
</span></span></code></div></div></pre>

سپس:

<pre class="overflow-visible! px-0!" data-start="1620" data-end="1663"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="@w-xl/main:top-9 sticky top-[calc(--spacing(9)+var(--header-height))]"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>pip install -r requirements.txt
</span></span></code></div></div></pre>

---

## ▶️ نحوه اجرا

از ریشه پروژه اجرا کنید:

<pre class="overflow-visible! px-0!" data-start="1713" data-end="1746"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="@w-xl/main:top-9 sticky top-[calc(--spacing(9)+var(--header-height))]"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>python -m scripts.run
</span></span></code></div></div></pre>

---

## 🧠 منطق اجرا

* برای هر **روز** یک Thread مجزا ایجاد می‌شود
* هر Thread:
  * Selenium Driver مستقل دارد
  * فرم جستجو را با تاریخ موردنظر پر می‌کند
  * تمام صفحات نتایج را پیمایش می‌کند
* در پایان:
  * داده‌ها تجمیع می‌شوند
  * گزارش آماری تولید می‌شود
  * خروجی در `output/` ذخیره می‌شود

---

## 📊 خروجی داده‌ها

* فرمت: `CSV`
* شامل اطلاعاتی مانند:
  * ستون‌های استخراج‌شده از جدول آگهی‌ها
  * تاریخ جستجو
  * شماره صفحه
  * نام Thread

نمونه نام فایل خروجی:

<pre class="overflow-visible! px-0!" data-start="2220" data-end="2266"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="@w-xl/main:top-9 sticky top-[calc(--spacing(9)+var(--header-height))]"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-text"><span><span>output/rrk_ads_20241223_153045.csv
</span></span></code></div></div></pre>

---

## 🪵 لاگ و دیباگ

* لاگ کامل اجرا در مسیر زیر ذخیره می‌شود:

<pre class="overflow-visible! px-0!" data-start="2335" data-end="2367"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="@w-xl/main:top-9 sticky top-[calc(--spacing(9)+var(--header-height))]"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-text"><span><span>logs/rrk_crawler.log
</span></span></code></div></div></pre>

* HTML صفحات برای بررسی ساختار سایت در مسیر زیر ذخیره می‌شوند:

<pre class="overflow-visible! px-0!" data-start="2433" data-end="2470"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="@w-xl/main:top-9 sticky top-[calc(--spacing(9)+var(--header-height))]"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-text"><span><span>data/page_Thread-1_0.html
</span></span></code></div></div></pre>

---

## ⚠️ نکات مهم

* تعداد Thread بالا ممکن است باعث:
  * بلاک شدن IP
  * Captcha
  * کندی سایت شود

    **پیشنهاد:** `3 تا 5 Thread`
* ساختار HTML سایت rrk.ir ممکن است تغییر کند

---

## 🧩 قابلیت توسعه

* افزودن:
  * ذخیره در دیتابیس (PostgreSQL / MongoDB)
  * خروجی JSON / Excel
  * Retry Mechanism
  * Proxy / Rotation
  * Scheduler (Airflow / Cron)

---

## 📌 هدف پروژه

این پروژه صرفاً با هدف **ارائه در فرآیند استخدام** و نمایش مهارت‌ها در حوزه‌های زیر توسعه داده شده است:

* Web Crawling
* Selenium
* Concurrency
* Logging
* Clean Code
* Debug-friendly Design

---

## 👤 نویسنده

**Hemin Saed**

Python Developer | Data & Web Crawling
