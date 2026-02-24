# ============================================
# REAL SCRAPER FOR NIGERIAN CAR SITES
# WITH ENHANCED JIJI SCRAPING AND DEBUG
# ============================================

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
import logging

from config import *

logger = logging.getLogger(__name__)

class NigerianCarScraper:
    def __init__(self):
        self.session = requests.Session()
        
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
            
            logger.info(f"  Found {len(topic_links)} total topics on page")
            
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
    
    def scrape_jiji_advanced(self):
        """Advanced requests-based Jiji scraper with better headers and cookie handling"""
        listings = []
        
        try:
            logger.info("🌐 Scraping Jiji with advanced headers...")
            
            # Create a fresh session
            session = requests.Session()
            
            # Step 1: Visit homepage to get cookies and look human
            home_headers = {
                'User-Agent': random.choice(USER_AGENT_LIST),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            logger.info("  👉 Visiting homepage to get cookies...")
            home_response = session.get("https://jiji.ng", headers=home_headers, timeout=REQUEST_TIMEOUT)
            logger.info(f"  Homepage response: {home_response.status_code}, length: {len(home_response.text)}")
            self.random_delay(3, 6)
            
            # Step 2: Now try search with advanced headers
            makes_to_search = [
                ('mercedes-benz', 'BENZ'),
                ('lexus', 'LEXUS'),
                ('toyota', 'TOYOTA')
            ]
            
            for make_slug, make_name in makes_to_search:
                logger.info(f"  👉 Searching {make_name}...")
                
                # Advanced headers that mimic a real browser
                search_headers = {
                    'User-Agent': random.choice(USER_AGENT_LIST),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://jiji.ng/',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                }
                
                url = f"https://jiji.ng/cars/{make_slug}"
                
                # Add random delay between searches
                self.random_delay(4, 8)
                
                response = session.get(url, headers=search_headers, timeout=REQUEST_TIMEOUT)
                
                # ========== DEBUG INFO ==========
                logger.info(f"  📊 Jiji response status: {response.status_code}")
                logger.info(f"  📊 Response length: {len(response.text)} characters")
                
                # Check for blocking indicators
                preview = response.text[:2000].lower()
                if "captcha" in preview:
                    logger.warning("  ⚠️ CAPTCHA detected! Jiji is blocking bots.")
                elif "verify" in preview:
                    logger.warning("  ⚠️ Verification page detected!")
                elif "robot" in preview or "automated" in preview:
                    logger.warning("  ⚠️ Bot detection page detected!")
                elif "no listings" in preview or "no results" in preview:
                    logger.warning("  ⚠️ Jiji says 'No listings' (silent block)")
                elif len(response.text) < 5000:
                    logger.warning(f"  ⚠️ Suspiciously small response ({len(response.text)} chars) - likely blocked")
                else:
                    logger.info(f"  ✅ Page loaded normally, looking for cars...")
                    
                # Save sample of response for debugging
                logger.debug(f"  Response sample: {response.text[:500]}")
                # ========== END DEBUG ==========
                
                if response.status_code != 200:
                    logger.warning(f"  ⚠️ Jiji returned {response.status_code} for {make_name}")
                    continue
                
                # Parse with html5lib
                soup = BeautifulSoup(response.text, 'html5lib')
                
                # Try multiple selectors for listings
                cards = []
                selectors = [
                    'div[class*="b-list-advert"]',
                    'div[class*="qa-advert"]',
                    'a[href*="/cars/"]',
                    'div.listing-card',
                    'div.advert-card',
                    'div[data-testid="listing"]',
                    'div.Listing__Container'
                ]
                
                for selector in selectors:
                    cards = soup.select(selector)
                    if cards:
                        logger.info(f"  ✅ Found {len(cards)} cards using selector: {selector}")
                        break
                
                if not cards:
                    # Try finding any div with car-like content
                    all_divs = soup.find_all('div')
                    cards = [div for div in all_divs if div.find('img') and len(div.text) > 50]
                    logger.info(f"  Found {len(cards)} potential cards using fallback method")
                
                logger.info(f"  Found {len(cards)} potential cards for {make_name}")
                
                for card in cards[:15]:  # First 15 per make
                    try:
                        # Extract title
                        title_elem = (card.find(['h3', 'h4', 'span'], class_=re.compile('title|name|description')) or 
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
                        price_elem = (card.find(['div', 'span'], class_=re.compile('price|amount')) or 
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
                        
                        listings.append({
                            'title': title,
                            'price': price,
                            'location': location,
                            'url': link,
                            'platform': f'Jiji.ng',
                            'description': title,
                            'make': car_make
                        })
                        
                        logger.info(f"  ✅ Jiji {make_name}: {title[:50]}...")
                        
                    except Exception as e:
                        logger.debug(f"  Error parsing card: {e}")
                        continue
                
                # Random delay between makes
                self.random_delay(3, 6)
            
            logger.info(f"✅ Jiji advanced scrape: Found {len(listings)} cars")
            
        except Exception as e:
            logger.error(f"❌ Jiji advanced scrape failed: {e}")
        
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
            
            logger.info(f"  OList response length: {len(response.text)}")
            soup = BeautifulSoup(response.text, 'html5lib')
            
            # Find listing items
            items = soup.find_all('div', class_=re.compile('listing|item|ad|card'))
            logger.info(f"  Found {len(items)} potential items")
            
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
        
        # 3. Jiji with advanced headers
        try:
            all_listings.extend(self.scrape_jiji_advanced())
        except Exception as e:
            logger.error(f"Jiji advanced method failed: {e}")
        
        # Remove duplicates (by URL)
        unique = []
        seen_urls = set()
        for listing in all_listings:
            if listing['url'] and listing['url'] not in seen_urls:
                seen_urls.add(listing['url'])
                unique.append(listing)
        
        logger.info(f"📊 TOTAL: {len(unique)} unique listings found")
        return unique
