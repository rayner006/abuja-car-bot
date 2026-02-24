# ============================================
# REAL SCRAPER FOR NIGERIAN CAR SITES
# WITH BROWSER AUTOMATION FOR JIJI
# ============================================

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

from config import *

logger = logging.getLogger(__name__)

class NigerianCarScraper:
    def __init__(self):
        self.session = requests.Session()
        self.driver = None
        
    def get_headers(self):
        """Random headers to avoid blocking"""
        return {
            'User-Agent': random.choice(USER_AGENT_LIST),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def random_delay(self, min_sec=2, max_sec=5):
        """Human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def setup_browser(self):
        """Setup undetected Chrome browser for Jiji"""
        try:
            logger.info("🔧 Setting up stealth browser...")
            options = uc.ChromeOptions()
            
            # Essential arguments to avoid detection
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            
            # Random user agent
            options.add_argument(f'--user-agent={random.choice(USER_AGENT_LIST)}')
            
            # Headless mode - faster but slightly more detectable
            # options.add_argument('--headless=new')
            
            # Initialize undetected driver
            self.driver = uc.Chrome(options=options)
            
            # Execute stealth scripts
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            """)
            
            logger.info("✅ Browser setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False
    
    def close_browser(self):
        """Close browser safely"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def scrape_nairaland(self):
        """Scrape Nairaland Autos section"""
        listings = []
        url = "https://www.nairaland.com/autos"
        
        try:
            logger.info("🌐 Scraping Nairaland...")
            self.random_delay()
            
            response = self.session.get(url, headers=self.get_headers(), timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Find all topic links
            all_links = soup.find_all('a', href=True)
            topic_links = [l for l in all_links if '/topic/' in l['href']]
            
            for link in topic_links[:30]:  # First 30 topics
                try:
                    title = link.text.strip()
                    if len(title) < 10:
                        continue
                    
                    # Check if in Abuja
                    title_lower = title.lower()
                    if not any(area in title_lower for area in ABUJA_AREAS):
                        continue
                    
                    # Check if target car
                    car_make = None
                    for make, keywords in TARGET_MAKES.items():
                        if any(kw in title_lower for kw in keywords):
                            car_make = make
                            break
                    
                    if not car_make:
                        continue
                    
                    # Extract price from title
                    price_match = re.search(r'[₦N]\s*([\d,]+)', title)
                    price = price_match.group(0) if price_match else "Contact for price"
                    
                    # Get full topic URL
                    href = link['href']
                    if href.startswith('/'):
                        href = 'https://www.nairaland.com' + href
                    
                    # Extract location more precisely
                    location = 'Abuja'
                    for area in ABUJA_AREAS:
                        if area in title_lower:
                            location = area.title()
                            break
                    
                    listings.append({
                        'title': title,
                        'price': price,
                        'location': location,
                        'url': href,
                        'platform': 'Nairaland',
                        'description': title,
                        'make': car_make
                    })
                    
                    logger.info(f"  ✅ Nairaland: {title[:60]}...")
                    
                except Exception as e:
                    continue
            
            logger.info(f"✅ Nairaland: Found {len(listings)} matching cars")
            
        except Exception as e:
            logger.error(f"❌ Nairaland scrape failed: {e}")
        
        return listings
    
    def scrape_jiji_with_browser(self):
        """Use real browser to beat Jiji anti-bot"""
        listings = []
        
        try:
            if not self.setup_browser():
                logger.error("❌ Could not start browser for Jiji")
                return []
            
            makes_to_search = [
                ('mercedes-benz', 'BENZ'),
                ('lexus', 'LEXUS'),
                ('toyota', 'TOYOTA')
            ]
            
            for make_slug, make_name in makes_to_search:
                url = f"https://jiji.ng/cars/{make_slug}"
                logger.info(f"🔍 Browser searching {make_name} on Jiji...")
                
                try:
                    # Navigate to page
                    self.driver.get(url)
                    
                    # Random wait to mimic human
                    self.random_delay(4, 8)
                    
                    # Scroll slowly like a human
                    for i in range(random.randint(2, 4)):
                        scroll = random.randint(300, 700)
                        self.driver.execute_script(f"window.scrollBy(0, {scroll});")
                        self.random_delay(0.5, 1.5)
                    
                    # Wait for listings to load
                    try:
                        WebDriverWait(self.driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='b-list-advert-base'], [class*='qa-advert']"))
                        )
                    except:
                        logger.warning(f"⚠️ No listings loaded for {make_name}, may be blocked")
                        continue
                    
                    # Get page source after JavaScript loads
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, 'html5lib')
                    
                    # Find all listing cards
                    cards = soup.find_all('div', class_=re.compile('b-list-advert-base|qa-advert-list-item'))
                    
                    if not cards:
                        # Try alternative selectors
                        cards = soup.find_all('a', href=re.compile(r'/cars/\d+'))
                    
                    logger.info(f"  Found {len(cards)} potential cards for {make_name}")
                    
                    for card in cards[:15]:  # First 15 per make
                        try:
                            # Extract title
                            title_elem = card.find(['div', 'h3', 'span'], class_=re.compile('title|name|description'))
                            if not title_elem:
                                title_elem = card.find('a')
                            if not title_elem:
                                continue
                                
                            title = title_elem.text.strip()
                            if len(title) < 5:
                                continue
                            
                            # Check Abuja location
                            card_text = card.text.lower()
                            if not any(area in card_text for area in ABUJA_AREAS):
                                continue
                            
                            # Extract price
                            price_elem = card.find(['div', 'span'], class_=re.compile('price|amount'))
                            price = price_elem.text.strip() if price_elem else "Contact"
                            
                            # Extract link
                            link_elem = card.find('a', href=True)
                            link = link_elem['href'] if link_elem else ""
                            if link and not link.startswith('http'):
                                link = 'https://jiji.ng' + link
                            
                            # Double-check make from title
                            title_lower = title.lower()
                            car_make = make_name  # Default to current search
                            
                            # Verify it's actually the right make
                            if make_name == 'BENZ' and not any(kw in title_lower for kw in TARGET_MAKES['BENZ']):
                                continue
                            if make_name == 'LEXUS' and not any(kw in title_lower for kw in TARGET_MAKES['LEXUS']):
                                continue
                            if make_name == 'TOYOTA' and not any(kw in title_lower for kw in TARGET_MAKES['TOYOTA']):
                                continue
                            
                            # Extract location
                            location = 'Abuja'
                            for area in ABUJA_AREAS:
                                if area in card_text:
                                    location = area.title()
                                    break
                            
                            listings.append({
                                'title': title,
                                'price': price,
                                'location': location,
                                'url': link,
                                'platform': f'Jiji.ng ({make_name})',
                                'description': title,
                                'make': car_make
                            })
                            
                            logger.info(f"  ✅ Jiji {make_name}: {title[:50]}...")
                            
                        except Exception as e:
                            continue
                    
                    # Random delay between makes
                    self.random_delay(5, 10)
                    
                except Exception as e:
                    logger.error(f"❌ Error scraping {make_name}: {e}")
                    continue
            
            logger.info(f"✅ Jiji browser scrape complete: {len(listings)} cars")
            
        except Exception as e:
            logger.error(f"❌ Jiji browser scrape failed: {e}")
        
        finally:
            self.close_browser()
        
        return listings
    
    def scrape_olist(self):
        """Scrape OList.ng with better error handling"""
        listings = []
        url = "https://olist.ng/cars/abuja"
        
        try:
            logger.info("🌐 Scraping OList...")
            self.random_delay()
            
            # Try with and without www
            urls_to_try = [
                "https://olist.ng/cars/abuja",
                "https://www.olist.ng/cars/abuja"
            ]
            
            response = None
            for test_url in urls_to_try:
                try:
                    response = self.session.get(test_url, headers=self.get_headers(), timeout=10)
                    if response.status_code == 200:
                        logger.info(f"✅ OList accessible via {test_url}")
                        break
                except:
                    continue
            
            if not response or response.status_code != 200:
                logger.warning("⚠️ OList not accessible, skipping...")
                return []
            
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Find listing items
            items = soup.find_all('div', class_=re.compile('listing|item|ad|card'))
            
            for item in items[:20]:
                try:
                    title_elem = item.find('h3') or item.find('h4') or item.find('a') or item.find('span', class_=re.compile('title'))
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()
                    
                    # Check if target car
                    title_lower = title.lower()
                    car_make = None
                    for make, keywords in TARGET_MAKES.items():
                        if any(kw in title_lower for kw in keywords):
                            car_make = make
                            break
                    
                    if not car_make:
                        continue
                    
                    # Extract price
                    price_elem = item.find('span', class_=re.compile('price')) or item.find('div', class_=re.compile('price'))
                    price = price_elem.text.strip() if price_elem else "Contact"
                    
                    # Extract link
                    link_elem = item.find('a', href=True)
                    link = link_elem['href'] if link_elem else ""
                    if link and not link.startswith('http'):
                        link = 'https://olist.ng' + link
                    
                    listings.append({
                        'title': title,
                        'price': price,
                        'location': 'Abuja',
                        'url': link,
                        'platform': 'OList.ng',
                        'description': title,
                        'make': car_make
                    })
                    
                    logger.info(f"  ✅ OList: {title[:50]}...")
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"⚠️ OList scrape failed (non-critical): {e}")
        
        logger.info(f"✅ OList: Found {len(listings)} matching cars")
        return listings
    
    def extract_location_from_text(self, text):
        """Extract Abuja area from text"""
        text_lower = text.lower()
        for area in ABUJA_AREAS:
            if area in text_lower:
                return area.title()
        return 'Abuja'
    
    def scrape_all(self):
        """Run all scrapers"""
        all_listings = []
        
        # 1. Nairaland (always works)
        try:
            all_listings.extend(self.scrape_nairaland())
        except Exception as e:
            logger.error(f"Nairaland failed: {e}")
        
        # 2. OList (if accessible)
        try:
            all_listings.extend(self.scrape_olist())
        except Exception as e:
            logger.warning(f"OList failed: {e}")
        
        # 3. Jiji with browser automation (best chance)
        try:
            all_listings.extend(self.scrape_jiji_with_browser())
        except Exception as e:
            logger.error(f"Jiji browser method failed: {e}")
        
        # Remove duplicates (by URL)
        unique = []
        seen_urls = set()
        for listing in all_listings:
            if listing['url'] and listing['url'] not in seen_urls:
                seen_urls.add(listing['url'])
                unique.append(listing)
        
        logger.info(f"📊 TOTAL: {len(unique)} unique listings found")
        return unique
