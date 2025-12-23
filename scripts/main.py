"""
Crawler حرفه‌ای برای استخراج آگهی‌های روزنامه رسمی ایران (rrk.ir)
استخراج موازی با استفاده از Threading - هر روز در یک Thread جداگانه

نسخه Multi-Threading برای سرعت بالا
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import jdatetime
from datetime import datetime
import pandas as pd
import json
import time
import logging
import os
from threading import Thread, Lock
from queue import Queue
import concurrent.futures

# تنظیمات logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)-10s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rrk_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class RRKCrawler:
    """کلاس اصلی Crawler با Selenium و پشتیبانی Threading"""
    
    def __init__(self, headless=True, thread_name=None):
        self.base_url = "https://rrk.ir"
        self.search_url = "https://rrk.ir/ords/r/rrs/rrs-front/داده-باز"
        self.all_ads = []
        self.headless = headless
        self.driver = None
        self.counter = 0
        self.thread_name = thread_name or "MainThread"
        self.lock = Lock()  # برای thread-safe operations
    
    def init_driver(self):
        """راه‌اندازی Selenium WebDriver با تنظیمات بهینه برای Headless"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-extensions')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--lang=fa-IR')
        chrome_options.add_argument('--accept-lang=fa-IR,fa')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        })
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            
            if self.headless:
                self.driver.set_window_size(1920, 1080)
            else:
                self.driver.maximize_window()
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info(f"✓ WebDriver راه‌اندازی شد (Thread: {self.thread_name})")
        except Exception as e:
            logging.error(f"خطا در راه‌اندازی WebDriver در {self.thread_name}: {e}")
            raise
    
    def wait_for_page_load(self, timeout=15):
        """انتظار برای بارگذاری کامل صفحه"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.execute_script('return typeof jQuery != "undefined" && jQuery.active == 0')
                )
            except:
                pass
            
            sleep_time = 2 if self.headless else 1
            time.sleep(sleep_time)
            
        except TimeoutException:
            logging.warning(f"تایم‌اوت در بارگذاری صفحه ({self.thread_name})")
    
    def fill_search_form(self, date_from, date_to=None):
        """پر کردن فرم جستجوی پیشرفته"""
        if not date_to:
            date_to = date_from
        
        try:
            logging.info(f"🔍 باز کردن صفحه جستجو ({self.thread_name})...")
            self.driver.get(self.search_url)
            self.wait_for_page_load(timeout=20)
            
            os.makedirs('screenshots', exist_ok=True)
            self.driver.save_screenshot(f'screenshots/step1_{self.thread_name}.png')
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            try:
                wait = WebDriverWait(self.driver, 20)
                
                date_from_field = wait.until(
                    EC.presence_of_element_located((By.ID, "P199_NEWSPAPERDATE_AZ"))
                )
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", date_from_field)
                time.sleep(0.5)
                
                date_from_field = wait.until(
                    EC.element_to_be_clickable((By.ID, "P199_NEWSPAPERDATE_AZ"))
                )
                
                date_to_field = self.driver.find_element(By.ID, "P199_NEWSPAPER_TA")
                
                self.driver.execute_script(f"arguments[0].value = '{date_from}';", date_from_field)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", date_from_field)
                logging.info(f"✓ تاریخ شروع: {date_from} ({self.thread_name})")
                
                self.driver.execute_script(f"arguments[0].value = '{date_to}';", date_to_field)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", date_to_field)
                logging.info(f"✓ تاریخ پایان: {date_to} ({self.thread_name})")
                
                time.sleep(1)
                self.driver.save_screenshot(f'screenshots/step2_{self.thread_name}.png')
                
                search_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'جستجو') or contains(@id, 'search') or contains(@class, 'search')]"))
                )
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                time.sleep(0.5)
                
                self.driver.execute_script("arguments[0].click();", search_button)
                logging.info(f"✓ دکمه جستجو کلیک شد ({self.thread_name})")
                
                self.wait_for_page_load(timeout=20)
                self.driver.save_screenshot(f'screenshots/step3_{self.thread_name}.png')
                
                return True
                
            except (NoSuchElementException, TimeoutException) as e:
                logging.error(f"خطا در پر کردن فرم ({self.thread_name}): {e}")
                return False
                
        except Exception as e:
            logging.error(f"خطای کلی در فرم ({self.thread_name}): {e}")
            return False
    
    def extract_ads_from_page(self):
        """استخراج آگهی‌ها از صفحه فعلی"""
        ads = []
        
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            os.makedirs('data', exist_ok=True)
            with open(f'data/page_{self.thread_name}_{self.counter}.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            self.counter += 1
            
            tables = soup.find_all('table')
            logging.info(f"📊 {len(tables)} جدول ({self.thread_name})")
            
            for table in tables:
                rows = table.find_all('tr')
                
                for i, row in enumerate(rows):
                    if i == 0:
                        continue
                    
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        ad_data = {
                            'ردیف': i,
                            'ستون_1': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                            'ستون_2': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                            'ستون_3': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                            'ستون_4': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                            'ستون_5': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                            'ستون_6': cells[5].get_text(strip=True) if len(cells) > 5 else '',
                        }
                        
                        link = row.find('a')
                        if link and link.get('href'):
                            ad_data['لینک'] = link['href']
                        
                        ads.append(ad_data)
            
            result_divs = soup.find_all('div', class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['result', 'item', 'card', 'row', 'ad']
            ))
            
            if not ads and result_divs:
                for div in result_divs[:10]:
                    text = div.get_text(strip=True)
                    if len(text) > 20:
                        ads.append({
                            'محتوا': text[:200],
                            'html': str(div)[:500]
                        })
            
        except Exception as e:
            logging.error(f"خطا در استخراج ({self.thread_name}): {e}")
        
        logging.info(f"✓ {len(ads)} آگهی استخراج شد ({self.thread_name})")
        return ads
    
    def check_next_page(self):
        """بررسی وجود صفحه بعدی"""
        try:
            wait = WebDriverWait(self.driver, 10)
            next_button = wait.until(
                EC.presence_of_element_located((By.XPATH, 
                    "//button[contains(text(), 'بعدی')] | //a[contains(text(), 'بعدی')] | //button[contains(@class, 'next')]"
                ))
            )
            
            if next_button.is_enabled() and next_button.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(0.5)
                
                self.driver.execute_script("arguments[0].click();", next_button)
                self.wait_for_page_load()
                return True
        except (NoSuchElementException, TimeoutException):
            logging.info(f"صفحه بعدی وجود ندارد ({self.thread_name})")
        
        return False
    
    def search_by_date(self, date):
        """جستجوی آگهی‌های یک تاریخ خاص"""
        logging.info(f"\n{'='*60}")
        logging.info(f"🔎 جستجو برای تاریخ: {date} ({self.thread_name})")
        logging.info(f"{'='*60}")
        
        all_date_ads = []
        
        if self.fill_search_form(date):
            page_num = 1
            
            while True:
                if page_num % 10 == 1:
                    time.sleep(6)
                
                logging.info(f"📄 صفحه {page_num} ({self.thread_name})...")
                ads = self.extract_ads_from_page()
                if ads:
                    for ad in ads:
                        ad['تاریخ_جستجو'] = date
                        ad['شماره_صفحه'] = page_num
                        ad['thread'] = self.thread_name
                    all_date_ads.extend(ads)
                
                if not self.check_next_page():
                    break
                
                page_num += 1
                time.sleep(0.1)
        
        logging.info(f"✓ {len(all_date_ads)} آگهی برای {date} ({self.thread_name})")
        return all_date_ads
    
    def crawl_date(self, date):
        """Crawl یک تاریخ خاص - برای استفاده در Thread"""
        try:
            self.init_driver()
            ads = self.search_by_date(date)
            return ads
        except Exception as e:
            logging.error(f"❌ خطا در crawl تاریخ {date} ({self.thread_name}): {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                logging.info(f"✓ WebDriver بسته شد ({self.thread_name})")


class ThreadedRRKCrawler:
    """کلاس مدیریت Crawler با Threading"""
    
    def __init__(self, headless=True, max_workers=5):
        self.headless = headless
        self.max_workers = max_workers
        self.all_results = []
        self.lock = Lock()
    
    def get_last_n_days(self, n=10):
        """دریافت n روز گذشته"""
        dates = []
        today = jdatetime.date.today()
        
        for i in range(1, n + 1):
            date = today - jdatetime.timedelta(days=i)
            dates.append(date.strftime('%Y/%m/%d'))
        
        logging.info(f"📅 تاریخ‌های هدف ({len(dates)} روز): {dates}")
        return dates
    
    def crawl_date_worker(self, date, thread_id):
        """Worker function برای هر thread"""
        thread_name = f"Thread-{thread_id}"
        logging.info(f"🚀 شروع Thread {thread_id} برای تاریخ {date}")
        
        crawler = RRKCrawler(headless=self.headless, thread_name=thread_name)
        ads = crawler.crawl_date(date)
        
        # Thread-safe اضافه کردن نتایج
        with self.lock:
            self.all_results.extend(ads)
        
        logging.info(f"✅ Thread {thread_id} تمام شد - {len(ads)} آگهی")
        return len(ads)
    
    def crawl_all_parallel(self, num_days=10):
        """Crawl موازی تمام روزها"""
        start_time = time.time()
        
        print("\n" + "="*70)
        print("🚀 شروع Crawling موازی روزنامه رسمی")
        print(f"   تعداد Threadها: {self.max_workers}")
        print(f"   تعداد روزها: {num_days}")
        print("="*70 + "\n")
        
        dates = self.get_last_n_days(num_days)
        
        # استفاده از ThreadPoolExecutor برای مدیریت بهتر
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # ارسال تمام taskها
            future_to_date = {
                executor.submit(self.crawl_date_worker, date, i): date 
                for i, date in enumerate(dates, 1)
            }
            
            # جمع‌آوری نتایج
            completed = 0
            for future in concurrent.futures.as_completed(future_to_date):
                date = future_to_date[future]
                try:
                    num_ads = future.result()
                    completed += 1
                    print(f"✓ [{completed}/{len(dates)}] تاریخ {date} تکمیل شد - {num_ads} آگهی")
                except Exception as e:
                    logging.error(f"❌ خطا در پردازش {date}: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "="*70)
        print("✅ Crawling موازی تکمیل شد!")
        print(f"   📊 مجموع آگهی‌ها: {len(self.all_results)}")
        print(f"   ⏱️  زمان کل: {duration:.2f} ثانیه")
        print(f"   ⚡ میانگین: {duration/len(dates):.2f} ثانیه به ازای هر روز")
        print("="*70 + "\n")
        
        df = pd.DataFrame(self.all_results) if self.all_results else pd.DataFrame()
        return df
    
    def save_results(self, df, formats=['csv', 'json', 'excel']):
        """ذخیره نتایج"""
        if df.empty:
            logging.warning("⚠️  دیتافریم خالی است")
            return
        
        os.makedirs('output', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if 'csv' in formats:
            csv_file = f'output/rrk_ads_{timestamp}.csv'
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"✅ CSV: {csv_file}")
        
        if 'json' in formats:
            json_file = f'output/rrk_ads_{timestamp}.json'
            df.to_json(json_file, orient='records', force_ascii=False, indent=2)
            print(f"✅ JSON: {json_file}")
        
        if 'excel' in formats:
            try:
                excel_file = f'output/rrk_ads_{timestamp}.xlsx'
                df.to_excel(excel_file, index=False, engine='openpyxl')
                print(f"✅ Excel: {excel_file}")
            except Exception as e:
                logging.warning(f"خطا در ذخیره Excel: {e}")
    
    def generate_report(self, df):
        """گزارش آماری کامل"""
        if df.empty:
            return
        
        print(f"\n📊 گزارش آماری کامل:")
        print(f"{'='*60}")
        print(f"   • تعداد کل آگهی‌ها: {len(df)}")
        print(f"   • ستون‌های موجود: {list(df.columns)}")
        
        if 'تاریخ_جستجو' in df.columns:
            print(f"   • تاریخ‌های جستجو شده: {df['تاریخ_جستجو'].nunique()}")
            print(f"\n   📅 توزیع بر اساس تاریخ:")
            for date, count in df['تاریخ_جستجو'].value_counts().sort_index().items():
                print(f"      - {date}: {count:,} آگهی")
        
        if 'thread' in df.columns:
            print(f"\n   🧵 توزیع بر اساس Thread:")
            for thread, count in df['thread'].value_counts().items():
                print(f"      - {thread}: {count:,} آگهی")
        
        print(f"{'='*60}\n")


def main():
    """تابع اصلی"""
    start_time = time.time()
    
    # ایجاد پوشه‌های لازم
    for folder in ['logs', 'data', 'screenshots', 'output']:
        os.makedirs(folder, exist_ok=True)
    
    print("\n" + "="*70)
    print("📰 Crawler روزنامه رسمی ایران (rrk.ir)")
    print("   🧵 نسخه Multi-Threading - پردازش موازی")
    print("="*70 + "\n")
    
    # تنظیمات
    NUM_DAYS = 10  # تعداد روزهای گذشته
    MAX_WORKERS = 5  # تعداد Thread همزمان (توصیه: 3-5 برای جلوگیری از بلاک شدن)
    HEADLESS = True  # حالت headless
    
    print(f"⚙️  تنظیمات:")
    print(f"   • تعداد روزها: {NUM_DAYS}")
    print(f"   • تعداد Thread همزمان: {MAX_WORKERS}")
    print(f"   • حالت Headless: {HEADLESS}")
    print()
    
    # اجرا
    crawler = ThreadedRRKCrawler(headless=HEADLESS, max_workers=MAX_WORKERS)
    
    try:
        df = crawler.crawl_all_parallel(num_days=NUM_DAYS)
        
        if not df.empty:
            crawler.generate_report(df)
            crawler.save_results(df)
            
            print(f"\n📋 نمونه داده (10 رکورد اول):")
            print(df.head(10).to_string())
        else:
            print("\n⚠️  هیچ آگهی یافت نشد!")
            print("\n💡 نکات عیب‌یابی:")
            print("   1. فایل‌های اسکرین‌شات در پوشه screenshots را بررسی کنید")
            print("   2. فایل‌های HTML در پوشه data را باز کنید")
            print("   3. لاگ‌ها را در پوشه logs بررسی کنید")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  عملیات توسط کاربر متوقف شد")
        logging.info("عملیات توسط کاربر متوقف شد")
    
    except Exception as e:
        logging.error(f"❌ خطای کلی: {e}", exc_info=True)
        print(f"\n❌ خطا: {e}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "="*70)
    print("✅ پایان برنامه")
    print(f"⏱️  زمان کل اجرا: {total_time:.2f} ثانیه ({total_time/60:.2f} دقیقه)")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()