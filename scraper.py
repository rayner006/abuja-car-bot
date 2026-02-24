# ============================================
# ULTIMATE SCRAPER WITH FREE PROXY ROTATION
# Combines undetected-chromedriver with free proxy pool
# ============================================

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import logging
import re
from bs4 import BeautifulSoup
import os
import itertools
import requests
from fake_useragent import UserAgent

from config import *

logger = logging.getLogger(__name__)

class NigerianCarScraper:
    def __init__(self):
        self.driver = None
        self.proxy_pool = []
        self.proxy_generator = None
        self.ua = UserAgent()
        
    def load_free_proxies(self):
        """Fetch free proxies from public sources"""
        try:
            logger.info("🌐 Loading free proxies...")
            
            # Get free proxies from multiple sources
            proxy_sources = [
                'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
                'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
                'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt'
            ]
            
            all_proxies = []
            for source in proxy_sources:
                try:
                    logger.info(f"  Fetching from {source.split('/')[2]}...")
                    response = requests.get(source, timeout=10)
                    if response.status_code == 200:
                        proxies = response.text.strip().split('\n')
                        # Clean proxies (remove whitespace)
                        proxies = [p.strip() for p in proxies if p.strip()]
                        all_proxies.extend(proxies)
                        logger.info(f"  Got {len(proxies)} proxies from {source.split('/')[2]}")
                except Exception as e:
                    logger.warning(f"  Failed to fetch from {source}: {e}")
                    continue
            
            # Remove duplicates
            all_proxies = list(set(all_proxies))
            logger.info(f"  Total unique proxies before testing: {len(all_proxies)}")
            
            # Test each proxy quickly (test first 50 for speed)
            working = []
            tested = 0
            for proxy in all_proxies[:50]:
                tested += 1
                try:
                    # Quick connectivity test
                    test = requests.get(
                        'http://httpbin.org/ip', 
                        proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'},
                        timeout=3
                    )
                    if test.status_code == 200:
                        working.append(proxy)
                        logger.info(f"  ✅ Proxy {proxy} works")
                except:
                    continue
            
            self.proxy_pool = working
            logger.info(f"✅ Loaded {len(working)} working free proxies out of {tested} tested")
            
            # Create rotation generator
            if self.proxy_pool:
                random.shuffle(self.proxy_pool)
                self.proxy_generator = itertools.cycle(self.proxy_pool)
                return True
            else:
                logger.warning("⚠️ No working proxies found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to load proxies: {e}")
            return False

    def get_next_proxy(self):
        """Get next proxy from rotation pool"""
        if hasattr(self, 'proxy_generator') and self.proxy_generator:
            return next(self.proxy_generator)
        return None

    def setup_browser_with_proxy(self, proxy_string=None):
        """Setup browser with specific proxy (optional)"""
        try:
            if proxy_string:
                logger.info(f"🔧 Setting up browser with proxy: {proxy_string}")
            else:
                logger.info("🔧 Setting up browser without proxy...")
            
            options = uc.ChromeOptions()
            
            # Essential arguments
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--disable-web-security')
            
            # Add proxy if provided
            if proxy_string:
                options.add_argument(f'--proxy-server=http://{proxy_string}')
            
            # Random user agent
            options.add_argument(f'--user-agent={self.ua.random}')
            
            # Language settings
            options.add_argument('--lang=en-US,en')
            
            # Initialize undetected Chrome
            self.driver = uc.Chrome(options=options)
            
            # Apply stealth JavaScript
            self.driver.execute_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Add realistic plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Set languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Add chrome runtime
                window.chrome = {
                    runtime: {}
                };
            """)
            
            if proxy_string:
                logger.info(f"✅ Browser setup complete with proxy: {proxy_string}")
            else:
                logger.info("✅ Browser setup complete without proxy")
            return True
            
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False

    def random_delay(self, min_sec=2, max_sec=5):
        """Human-like delay with random jitter"""
        time.sleep(random.uniform(min_sec, max_sec))

    def human_scroll(self):
        """Scroll like a human with natural pauses"""
        scroll_amount = random.randint(300, 700)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        self.random_delay(0.5, 1.5)
        
        # Sometimes scroll back a bit (humans overshoot)
        if random.random() > 0.7:
            scroll_back = random.randint(50, 150)
            self.driver.execute_script(f"window.scrollBy(0, -{scroll_back});")
            self.random_delay(0.3, 0.8)

    def calculate_distress_score(self, text):
        """Calculate distress score based on keywords"""
        text_lower = text.lower()
        score = 0
        matched = []
        
        for keyword, weight in ALL_DISTRESS.items():
            if keyword in text_lower:
                score += weight
                matched.append(keyword)
        
        return score, matched

    def scrape_jiji_stealth(self):
        """Jiji scraper with stealth + FREE PROXY ROTATION"""
        listings = []
        
        try:
            # Load free proxies first
            if not self.load_free_proxies():
                logger.warning("⚠️ No free proxies available, will try without proxy...")
            
            makes_to_search = [
                ('mercedes-benz', 'BENZ'),
                ('lexus', 'LEXUS'),
                ('toyota', 'TOYOTA')
            ]
            
            for make_slug, make_name in makes_to_search:
                logger.info(f"🎯 Targeting {make_name} in Abuja...")
                
                # Try with different proxies (or without)
                max_attempts = max(3, len(self.proxy_pool)) if self.proxy_pool else 1
                
                for attempt in range(max_attempts):
                    proxy = self.get_next_proxy() if self.proxy_pool else None
                    
                    if proxy:
                        logger.info(f"  Attempt {attempt+1}/{max_attempts} for {make_name} with proxy: {proxy}")
                    else:
                        logger.info(f"  Attempt {attempt+1}/{max_attempts} for {make_name} without proxy")
                    
                    try:
                        # Setup browser with this proxy (or without)
                        if not self.setup_browser_with_proxy(proxy):
                            logger.warning("  Browser setup failed, trying next...")
                            continue
                        
                        url = f"https://jiji.ng/cars/{make_slug}"
                        logger.info(f"  Navigating to {url}")
                        
                        # Set page load timeout
                        self.driver.set_page_load_timeout(30)
                        
                        # Navigate to page
                        self.driver.get(url)
                        
                        # Random delay after load
                        self.random_delay(4, 8)
                        
                        # Scroll naturally
                        self.human_scroll()
                        
                        # Wait for content
                        time.sleep(random.uniform(2, 4))
                        
                        # Get page source and analyze
                        page_source = self.driver.page_source
                        page_length = len(page_source)
                        logger.info(f"  📊 Page length: {page_length} chars")
                        
                        # Check for blocking indicators
                        page_lower = page_source.lower()
                        if "captcha" in page_lower:
                            logger.warning(f"  ⚠️ Captcha detected")
                            self.driver.quit()
                            continue
                        elif "403" in page_lower or "forbidden" in page_lower:
                            logger.warning(f"  ⚠️ 403 Forbidden detected")
                            self.driver.quit()
                            continue
                        elif page_length < 50000:
                            logger.warning(f"  ⚠️ Suspiciously small page ({page_length} chars)")
                            self.driver.quit()
                            continue
                        
                        # Parse with BeautifulSoup
                        soup = BeautifulSoup(page_source, 'html5lib')
                        
                        # Try multiple selectors for listings
                        cards = []
                        selectors = [
                            'div[class*="b-list-advert-base"]',
                            'div[class*="qa-advert-list-item"]',
                            'div[class*="listing-card"]',
                            'a[href*="/cars/"][class*="advert"]',
                            'div[data-testid="listing"]',
                            'div.Listing__Container'
                        ]
                        
                        for selector in selectors:
                            cards = soup.select(selector)
                            if cards:
                                logger.info(f"  Found {len(cards)} cards using: {selector}")
                                break
                        
                        if not cards:
                            # Try fallback - look for divs with images
                            all_divs = soup.find_all('div')
                            cards = [div for div in all_divs if div.find('img') and len(div.text) > 100]
                            logger.info(f"  Found {len(cards)} cards using fallback method")
                        
                        for card in cards[:15]:  # First 15 per make
                            try:
                                # Extract title
                                title_elem = (card.find(['h3', 'h4', 'span'], 
                                                        class_=re.compile('title|name|description')) or 
                                             card.find('a') or 
                                             card)
                                title = title_elem.text.strip() if title_elem else ""
                                
                                if len(title) < 10:
                                    continue
                                
                                # Check Abuja location
                                card_text = card.text.lower()
                                if not any(area in card_text for area in ABUJA_AREAS):
                                    continue
                                
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
                                price_elem = (card.find(['div', 'span'], 
                                                         class_=re.compile('price|amount')) or 
                                             card.find(['div', 'span'], string=re.compile(r'[₦N]')))
                                price = price_elem.text.strip() if price_elem else "Contact"
                                
                                # Extract link
                                link_elem = card.find('a', href=True)
                                link = link_elem['href'] if link_elem else ""
                                if link and not link.startswith('http'):
                                    link = 'https://jiji.ng' + link
                                
                                # Extract location
                                location = 'Abuja'
                                for area in ABUJA_AREAS:
                                    if area in card_text:
                                        location = area.title()
                                        break
                                
                                # Calculate distress score
                                full_text = title + " " + card_text
                                distress_score, matched = self.calculate_distress_score(full_text)
                                
                                listings.append({
                                    'title': title,
                                    'price': price,
                                    'location': location,
                                    'url': link,
                                    'platform': 'Jiji.ng (Stealth+Proxy)',
                                    'description': title,
                                    'make': car_make,
                                    'distress_score': distress_score,
                                    'distress_keywords': matched[:3] if matched else []
                                })
                                
                                logger.info(f"  ✅ Found: {title[:60]}... (Score: {distress_score})")
                                
                            except Exception as e:
                                continue
                        
                        # Success! Break out of retry loop
                        self.driver.quit()
                        break
                        
                    except Exception as e:
                        logger.error(f"  Attempt {attempt+1} failed: {e}")
                        if self.driver:
                            try:
                                self.driver.quit()
                            except:
                                pass
                        self.random_delay(3, 6)
                
                # Random delay between makes
                self.random_delay(5, 10)
            
            logger.info(f"✅ Jiji stealth scrape complete: {len(listings)} cars found")
            
        except Exception as e:
            logger.error(f"❌ Jiji stealth scrape failed: {e}")
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
        
        return listings

    def scrape_nairaland(self):
        """Scrape Nairaland Autos section"""
        listings = []
        url = "https://www.nairaland.com/autos"
        
        try:
            logger.info("🌐 Scraping Nairaland...")
            self.random_delay()
            
            headers = {'User-Agent': self.ua.random}
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Find all topic links
            all_links = soup.find_all('a', href=True)
            topic_links = [l for l in all_links if '/topic/' in l['href']]
            
            for link in topic_links[:30]:
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
                    
                    # Extract price
                    price_match = re.search(r'[₦N]\s*([\d,]+)', title)
                    price = price_match.group(0) if price_match else "Contact"
                    
                    # Get URL
                    href = link['href']
                    if href.startswith('/'):
                        href = 'https://www.nairaland.com' + href
                    
                    # Calculate distress score
                    distress_score, matched = self.calculate_distress_score(title)
                    
                    listings.append({
                        'title': title,
                        'price': price,
                        'location': 'Abuja',
                        'url': href,
                        'platform': 'Nairaland',
                        'description': title,
                        'make': car_make,
                        'distress_score': distress_score,
                        'distress_keywords': matched[:3] if matched else []
                    })
                    
                    logger.info(f"  ✅ Nairaland: {title[:60]}...")
                    
                except Exception:
                    continue
            
            logger.info(f"✅ Nairaland: Found {len(listings)} cars")
            
        except Exception as e:
            logger.error(f"❌ Nairaland failed: {e}")
        
        return listings

    def scrape_olist(self):
        """Scrape OList.ng"""
        listings = []
        url = "https://olist.ng/cars/abuja"
        
        try:
            logger.info("🌐 Scraping OList...")
            self.random_delay()
            
            headers = {'User-Agent': self.ua.random}
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                logger.warning("⚠️ OList not accessible")
                return []
            
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Find listing items
            items = soup.find_all('div', class_=re.compile('listing|item|ad|card'))
            
            for item in items[:20]:
                try:
                    title_elem = item.find('h3') or item.find('h4') or item.find('a')
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
                    
                    # Calculate distress score
                    distress_score, matched = self.calculate_distress_score(title)
                    
                    listings.append({
                        'title': title,
                        'price': price,
                        'location': 'Abuja',
                        'url': link,
                        'platform': 'OList.ng',
                        'description': title,
                        'make': car_make,
                        'distress_score': distress_score,
                        'distress_keywords': matched[:3] if matched else []
                    })
                    
                    logger.info(f"  ✅ OList: {title[:60]}...")
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"⚠️ OList scrape failed: {e}")
        
        logger.info(f"✅ OList: Found {len(listings)} cars")
        return listings

    def scrape_all(self):
        """Run all scrapers"""
        all_listings = []
        
        # 1. Jiji with stealth + proxies (primary)
        try:
            jiji_results = self.scrape_jiji_stealth()
            all_listings.extend(jiji_results)
        except Exception as e:
            logger.error(f"Jiji stealth failed: {e}")
        
        # 2. Nairaland (backup)
        try:
            nairaland_results = self.scrape_nairaland()
            all_listings.extend(nairaland_results)
        except Exception as e:
            logger.error(f"Nairaland failed: {e}")
        
        # 3. OList (if available)
        try:
            olist_results = self.scrape_olist()
            all_listings.extend(olist_results)
        except Exception as e:
            logger.warning(f"OList failed: {e}")
        
        # Remove duplicates
        unique = []
        seen_urls = set()
        for listing in all_listings:
            if listing['url'] and listing['url'] not in seen_urls:
                seen_urls.add(listing['url'])
                unique.append(listing)
        
        logger.info(f"📊 TOTAL: {len(unique)} unique listings found")
        return unique
