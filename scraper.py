# ============================================
# STEP 1: BASIC BROWSER VERSION WITH STEALTH
# Undetected Chrome + selenium-stealth
# ============================================

import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import logging
import re
from bs4 import BeautifulSoup
import os

from config import *

logger = logging.getLogger(__name__)

class NigerianCarScraper:
    def __init__(self):
        self.driver = None
        
    def setup_browser(self):
        """Setup undetected Chrome browser with stealth"""
        try:
            logger.info("🔧 Setting up undetected Chrome with stealth...")
            
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            self.driver = uc.Chrome(options=options)
            
            # Apply selenium-stealth (CRITICAL for bypassing detection)
            stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            logger.info("✅ Browser setup complete with stealth")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False
    
    def random_delay(self, min_sec=2, max_sec=5):
        """Human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def human_scroll(self):
        """Scroll like a human"""
        scroll1 = random.randint(300, 500)
        scroll2 = random.randint(100, 300)
        
        self.driver.execute_script(f"window.scrollBy(0, {scroll1});")
        self.random_delay(0.5, 1.5)
        self.driver.execute_script(f"window.scrollBy(0, {scroll2});")
        self.random_delay(0.3, 1)
    
    def scrape_jiji_basic(self):
        """Basic browser-based Jiji scraper with stealth"""
        listings = []
        
        try:
            if not self.setup_browser():
                return []
            
            makes_to_search = [
                ('mercedes-benz', 'BENZ'),
                ('lexus', 'LEXUS'),
                ('toyota', 'TOYOTA')
            ]
            
            for make_slug, make_name in makes_to_search:
                url = f"https://jiji.ng/cars/{make_slug}"
                logger.info(f"🔍 Browser searching {make_name}...")
                
                try:
                    # Navigate to page
                    self.driver.get(url)
                    self.random_delay(5, 8)  # Longer initial delay
                    
                    # Scroll like a human
                    self.human_scroll()
                    
                    # Get page source
                    page_source = self.driver.page_source
                    page_length = len(page_source)
                    logger.info(f"  Page length: {page_length} chars")
                    
                    # Check if we're blocked
                    if "captcha" in page_source.lower():
                        logger.warning(f"  ⚠️ Captcha detected for {make_name}")
                        continue
                    elif "403" in page_source:
                        logger.warning(f"  ⚠️ 403 Forbidden for {make_name}")
                        continue
                    
                    soup = BeautifulSoup(page_source, 'html5lib')
                    
                    # Try multiple selectors for listings
                    cards = []
                    selectors = [
                        'div[class*="b-list-advert"]',
                        'div[class*="qa-advert"]',
                        'div[class*="listing-card"]',
                        'a[href*="/cars/"]'
                    ]
                    
                    for selector in selectors:
                        cards = soup.select(selector)
                        if cards:
                            logger.info(f"  Found {len(cards)} cards using {selector}")
                            break
                    
                    for card in cards[:10]:
                        try:
                            # Extract title
                            title_elem = card.find(['h3', 'span'], class_=re.compile('title|name'))
                            if not title_elem:
                                continue
                            title = title_elem.text.strip()
                            
                            if len(title) < 5:
                                continue
                            
                            # Check Abuja
                            card_text = card.text.lower()
                            if not any(area in card_text for area in ABUJA_AREAS):
                                continue
                            
                            # Check make
                            title_lower = title.lower()
                            car_make = None
                            for m, keywords in TARGET_MAKES.items():
                                if any(kw in title_lower for kw in keywords):
                                    car_make = m
                                    break
                            
                            if not car_make:
                                continue
                            
                            # Extract price
                            price_elem = card.find(['div', 'span'], class_=re.compile('price|amount'))
                            price = price_elem.text.strip() if price_elem else "Contact"
                            
                            # Extract link
                            link_elem = card.find('a', href=True)
                            link = link_elem['href'] if link_elem else ""
                            
                            listings.append({
                                'title': title,
                                'price': price,
                                'location': 'Abuja',
                                'url': link if link.startswith('http') else f"https://jiji.ng{link}",
                                'platform': 'Jiji.ng (Stealth)',
                                'description': title,
                                'make': car_make
                            })
                            
                            logger.info(f"  ✅ Found: {title[:50]}...")
                            
                        except Exception as e:
                            continue
                    
                    self.random_delay(4, 7)
                    
                except Exception as e:
                    logger.error(f"Error on {make_name}: {e}")
                    continue
            
            logger.info(f"✅ Found {len(listings)} cars from Jiji")
            
        except Exception as e:
            logger.error(f"❌ Jiji browser scrape failed: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
        
        return listings
    
    def scrape_nairaland(self):
        """Keep your existing Nairaland code"""
        # Your existing Nairaland code here
        return []
    
    def scrape_olist(self):
        """Keep your existing OList code"""
        # Your existing OList code here
        return []
    
    def scrape_all(self):
        """Run all scrapers"""
        all_listings = []
        
        # 1. Try Jiji with stealth browser first
        try:
            jiji_results = self.scrape_jiji_basic()
            all_listings.extend(jiji_results)
            logger.info(f"📊 Jiji returned {len(jiji_results)} cars")
        except Exception as e:
            logger.error(f"Jiji failed: {e}")
        
        # 2. Nairaland backup
        try:
            nairaland_results = self.scrape_nairaland()
            all_listings.extend(nairaland_results)
            logger.info(f"📊 Nairaland returned {len(nairaland_results)} cars")
        except Exception as e:
            logger.error(f"Nairaland failed: {e}")
        
        # Remove duplicates
        unique = []
        seen_urls = set()
        for listing in all_listings:
            if listing['url'] and listing['url'] not in seen_urls:
                seen_urls.add(listing['url'])
                unique.append(listing)
        
        logger.info(f"📊 TOTAL: {len(unique)} unique listings found")
        return unique
