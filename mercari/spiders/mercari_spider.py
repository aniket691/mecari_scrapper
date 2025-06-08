import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

class MercariSpider(scrapy.Spider):
    name = "mercari_spider"
    allowed_domains = ["jp.mercari.com"]
    
    def __init__(self):
        chrome_options = Options()
        # Remove headless mode to see what's happening
        #chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.items = []
        super().__init__()

    def start_requests(self):
        # Test with a simple URL first
        url = "https://jp.mercari.com/search?keyword=pokemon&category_id=2"
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        try:
            self.driver.get(response.url)
            self.logger.info("Page loaded, waiting for content...")
            
            # Wait longer for initial load
            time.sleep(15)
            
            # Save page source for debugging
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Try multiple selectors
            selectors = [
                "//a[contains(@href, '/item/')]",  # XPath for item links
                "//mer-item-thumbnail",  # Custom element
                "//div[contains(@class, 'item-cell')]"  # Generic item container
            ]
            
            items_found = False
            for selector in selectors:
                try:
                    items = self.driver.find_elements(By.XPATH, selector)
                    if items:
                        self.logger.info(f"Found {len(items)} items using selector: {selector}")
                        items_found = True
                        
                        for item in items:
                            try:
                                # Try to get item details
                                item_url = item.get_attribute('href') or item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                                
                                data = {
                                    'url': item_url,
                                    'html': item.get_attribute('outerHTML'),  # Save HTML for debugging
                                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                                }
                                
                                # Try to get more details if available
                                try:
                                    data['title'] = item.get_attribute('item-name') or item.find_element(By.CSS_SELECTOR, '[class*="name"]').text
                                except: pass
                                
                                try:
                                    data['price'] = item.get_attribute('price') or item.find_element(By.CSS_SELECTOR, '[class*="price"]').text
                                except: pass
                                
                                try:
                                    data['image'] = item.find_element(By.TAG_NAME, 'img').get_attribute('src')
                                except: pass
                                
                                self.items.append(data)
                                self.logger.info(f"Scraped item: {data.get('url', 'No URL')}")
                                
                            except Exception as e:
                                self.logger.error(f"Error extracting item details: {str(e)}")
                        break
                except Exception as e:
                    self.logger.error(f"Error with selector {selector}: {str(e)}")
            
            if not items_found:
                self.logger.error("No items found with any selector")
            
            # Save results
            if self.items:
                with open('items.json', 'w', encoding='utf-8') as f:
                    json.dump(self.items, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Saved {len(self.items)} items to items.json")
            
        except Exception as e:
            self.logger.error(f"Error in parse method: {str(e)}")
            
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 3,
        'LOG_LEVEL': 'INFO'
    }
