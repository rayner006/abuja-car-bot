# ============================================
# ULTIMATE SCRAPER WITH SELENIUM-WIRE + PROXIES
# Combines undetected-chromedriver with authenticated proxies
# ============================================

# UPDATED IMPORTS
import undetected_chromedriver as uc
from seleniumwire import webdriver as wire_webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import random
import logging
import re
from bs4 import BeautifulSoup
import os
import itertools
from fake_useragent import UserAgent

from config import *

logger = logging.getLogger(__name__)

class NigerianCarScraper:
    def __init__(self):
        self.driver = None
        self.proxy_pool = []
        self.proxy_generator = None
        self.ua = UserAgent()
        
    def load_proxy_pool(self):
        """
        Load proxies from environment variable or file
        Format: http://username:password@host:port
        """
        try:
            # Check if proxy list is set in environment
            proxy_string = os.environ.get('PROXY_LIST')
            
            if proxy_string:
                # Parse comma-separated proxies
                self.proxy_pool = [p.strip() for p in proxy_string.split(',')]
                logger.info(f"✅ Loaded {len(self.proxy_pool)} proxies from environment")
            else:
                # Use free proxies for testing (these are examples - replace with real ones)
                logger.warning("⚠️ No proxies in environment, using test proxies")
                self.proxy_pool = [
                    "http://20.44.189.184:3129",
                    "http://23.247.136.245:80",
                    "http://133.130.107.58:80",
                ]
            
            # Shuffle and create rotation generator
            random.shuffle(self.proxy_pool)
            self.proxy_generator = itertools.cycle(self.proxy_pool)
            
        except Exception as e:
            logger.error(f"❌ Failed to load proxy pool: {e}")
            self.proxy_pool = []
    
    def get_next_proxy(self):
        """Get next proxy from rotation pool"""
        if self.proxy_generator:
            return next(self.proxy_generator)
        return None
    
    def setup_stealth_browser(self, proxy_string=None):
        """
        Setup undetected Chrome with selenium-wire for stealth + proxies
        This combines both technologies to bypass Jiji's blocks
        """
        try:
            logger.info("🔧 Setting up stealth browser with selenium-wire...")
            
            # Configure selenium-wire options for proxy
            seleniumwire_options = {}
            
            if proxy_string:
                seleniumwire_options = {
                    'proxy': {
                        'http': proxy_string,
                        'https': proxy_string,
                        'no_proxy': 'localhost,127.0.0.1',
                    },
                    'verify_ssl': False,  # Some proxies have SSL issues
                }
                # Log only host:port, hide credentials
                clean_proxy = proxy_string.split('@')[-1] if '@' in proxy_string else proxy_string
                logger.info(f"  Using proxy: {clean_proxy}")
            
            # Configure undetected Chrome options
            chrome_options = uc.ChromeOptions()
            
            # Essential stealth arguments
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            chrome_options.add_argument('--disable-javascript')  # Some sites detect JS patterns
            
            # Random user agent
            chrome_options.add_argument(f'--user-agent={self.ua.random}')
            
            # Additional arguments for stealth
            chrome_options.add_argument('--lang=en-US,en')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            
            # Initialize the driver with both undetected-chrome and selenium-wire
            # This is the magic combination!
            self.driver = uc.Chrome(
                options=chrome_options,
                seleniumwire_options=seleniumwire_options
            )
            
            # Execute stealth JavaScript
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
                
                // Add chrome runtime (makes it look like real Chrome)
                window.chrome = {
                    runtime: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            logger.info("✅ Stealth browser setup complete" + 
                       (" with proxy" if proxy_string else ""))
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
    
    def human_mouse_movement(self, element=None):
        """
        Simulate human mouse movement
        Note: This is basic - for full humanization, we'd need more complex patterns
        """
        try:
            if element:
                # Move to element with random offset
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element_with_offset(
                    element, 
                    random.randint(5, 15), 
                    random.randint(5, 15)
                ).perform()
                self.random_delay(0.2, 0.5)
        except:
            pass
    
    def scrape_jiji_stealth(self):
        """
        Ultimate Jiji scraper with:
        - Undetected ChromeDriver (evades detection)
        - Selenium-wire (authenticated proxies)
        - Human-like behavior
        - Multiple retry attempts
        """
        listings = []
        
        try:
            # Load proxy pool first
            self.load_proxy_pool()
            
            makes_to_search = [
                ('mercedes-benz', 'BENZ'),
                ('lexus', 'LEXUS'),
                ('toyota', 'TOYOTA')
            ]
            
            for make_slug, make_name in makes_to_search:
                logger.info(f"🎯 Targeting {make_name} in Abuja...")
                
                # Try up to 3 different proxies for each make
                for attempt in range(3):
                    proxy = self.get_next_proxy()
                    logger.info(f"  Attempt {attempt+1}/3 for {make_name}")
                    
                    try:
                        # Setup browser with this proxy
                        if not self.setup_stealth_browser(proxy):
                            logger.warning("  Browser setup failed, trying next proxy...")
                            continue
                        
                        url = f"https://jiji.ng/cars/{make_slug}"
                        logger.info(f"  Navigating to {url}")
                        
                        # Set page load timeout
                        self.driver.set_page_load_timeout(30)
                        
                        # Navigate to page
                        self.driver.get(url)
                        
                        # Random delay after load (human behavior)
                        self.random_delay(4, 8)
                        
                        # Scroll naturally
                        self.human_scroll()
                        
                        # Wait for content to load
                        time.sleep(random.uniform(2, 4))
                        
                        # Get page source and analyze
                        page_source = self.driver.page_source
                        page_length = len(page_source)
                        logger.info(f"  📊 Page length: {page_length} chars")
                        
                        # Check for blocking indicators
                        if "captcha" in page_source.lower():
                            logger.warning(f"  ⚠️ Captcha detected with this proxy")
                            self.driver.quit()
                            continue
                        elif "403" in page_source or "forbidden" in page_source.lower():
                            logger.warning(f"  ⚠️ 403 Forbidden with this proxy")
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
                            # Try finding any div with car-like content
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
    
    def scrape_nairaland(self):
        """Keep your existing Nairaland code"""
        listings = []
        url = "https://www.nairaland.com/autos"
        
        try:
            logger.info("🌐 Scraping Nairaland...")
            self.random_delay()
            
            response = requests.get(url, headers={'User-Agent': self.ua.random}, timeout=REQUEST_TIMEOUT)
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
                    
                except Exception:
                    continue
            
            logger.info(f"✅ Nairaland: Found {len(listings)} cars")
            
        except Exception as e:
            logger.error(f"❌ Nairaland failed: {e}")
        
        return listings
    
    def scrape_olist(self):
        """Keep your existing OList code"""
        # Your existing OList code here
        return []
    
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
