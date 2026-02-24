# ============================================
# REAL SCRAPER FOR NIGERIAN CAR SITES
# ============================================

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
import logging
from fake_useragent import UserAgent

from config import *

logger = logging.getLogger(__name__)

class NigerianCarScraper:
    def __init__(self):
        self.ua = UserAgent()
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
    
    def random_delay(self):
        """Human-like delay"""
        time.sleep(random.uniform(2, 5))
    
    def scrape_nairaland(self):
        """Scrape Nairaland Autos section"""
        listings = []
        url = "https://www.nairaland.com/autos"
        
        try:
            logger.info("🌐 Scraping Nairaland...")
            self.random_delay()
            
            response = self.session.get(url, headers=self.get_headers(), timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all topic links
            all_links = soup.find_all('a', href=True)
            topic_links = [l for l in all_links if '/topic/' in l['href'] and 'autos' in str(l).lower()]
            
            for link in topic_links[:20]:  # First 20 topics
                try:
                    title = link.text.strip()
                    
                    # Check if in Abuja
                    if not any(area in title.lower() for area in ABUJA_AREAS):
                        continue
                    
                    # Check if target car
                    car_make = None
                    for make, keywords in TARGET_MAKES.items():
                        if any(kw in title.lower() for kw in keywords):
                            car_make = make
                            break
                    
                    if not car_make:
                        continue
                    
                    # Extract price from title
                    price_match = re.search(r'₦\s*([\d,]+)', title)
                    price = price_match.group(0) if price_match else "Contact for price"
                    
                    # Get full topic URL
                    href = link['href']
                    if href.startswith('/'):
                        href = 'https://www.nairaland.com' + href
                    
                    # Get description from topic preview if available
                    description = title  # Default
                    
                    listings.append({
                        'title': title,
                        'price': price,
                        'location': self.extract_location_from_text(title),
                        'url': href,
                        'platform': 'Nairaland',
                        'description': title,
                        'make': car_make
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing Nairaland link: {e}")
                    continue
            
            logger.info(f"✅ Nairaland: Found {len(listings)} matching cars")
            
        except Exception as e:
            logger.error(f"❌ Nairaland scrape failed: {e}")
        
        return listings
    
    def scrape_jiji(self):
        """Scrape Jiji.ng - More complex with anti-bot"""
        listings = []
        
        # Jiji search URLs for different makes
        search_urls = [
            "https://jiji.ng/cars/mercedes-benz",
            "https://jiji.ng/cars/lexus",
            "https://jiji.ng/cars/toyota"
        ]
        
        for base_url in search_urls:
            try:
                logger.info(f"🌐 Scraping {base_url}...")
                self.random_delay()
                
                response = self.session.get(base_url, headers=self.get_headers(), timeout=REQUEST_TIMEOUT)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find listing cards - Jiji uses various classes
                cards = soup.find_all('div', class_=re.compile('b-list-advert-base|qa-advert-list-item'))
                
                for card in cards[:10]:  # First 10 per category
                    try:
                        # Extract title
                        title_elem = card.find('div', class_=re.compile('title')) or card.find('h3')
                        if not title_elem:
                            continue
                        title = title_elem.text.strip()
                        
                        # Check Abuja location
                        page_text = card.text.lower()
                        if not any(area in page_text for area in ABUJA_AREAS):
                            continue
                        
                        # Extract price
                        price_elem = card.find('div', class_=re.compile('price')) or card.find('span', class_=re.compile('price'))
                        price = price_elem.text.strip() if price_elem else "Contact"
                        
                        # Extract link
                        link_elem = card.find('a', href=True)
                        link = link_elem['href'] if link_elem else ""
                        if link and not link.startswith('http'):
                            link = 'https://jiji.ng' + link
                        
                        # Determine make from title
                        car_make = None
                        for make, keywords in TARGET_MAKES.items():
                            if any(kw in title.lower() for kw in keywords):
                                car_make = make
                                break
                        
                        if car_make:
                            listings.append({
                                'title': title,
                                'price': price,
                                'location': self.extract_location_from_text(title + " " + page_text),
                                'url': link,
                                'platform': 'Jiji.ng',
                                'description': title,
                                'make': car_make
                            })
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Jiji scrape failed for {base_url}: {e}")
                continue
        
        logger.info(f"✅ Jiji: Found {len(listings)} matching cars")
        return listings
    
    def scrape_olist(self):
        """Scrape OList.ng"""
        listings = []
        url = "https://olist.ng/cars/abuja"
        
        try:
            logger.info("🌐 Scraping OList...")
            self.random_delay()
            
            response = self.session.get(url, headers=self.get_headers(), timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find listing items
            items = soup.find_all('div', class_=re.compile('listing|item|ad'))
            
            for item in items[:20]:
                try:
                    title_elem = item.find('h3') or item.find('h4') or item.find('a')
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()
                    
                    # Check if target car
                    car_make = None
                    for make, keywords in TARGET_MAKES.items():
                        if any(kw in title.lower() for kw in keywords):
                            car_make = make
                            break
                    
                    if not car_make:
                        continue
                    
                    # Location already filtered by URL (Abuja)
                    
                    # Extract price
                    price_elem = item.find('span', class_=re.compile('price')) or item.find('div', class_=re.compile('price'))
                    price = price_elem.text.strip() if price_elem else "Contact"
                    
                    # Extract link
                    link = title_elem['href'] if title_elem.name == 'a' and title_elem.has_attr('href') else ""
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
                    
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"❌ OList scrape failed: {e}")
        
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
        
        # Scrape from all platforms
        all_listings.extend(self.scrape_nairaland())
        all_listings.extend(self.scrape_olist())
        all_listings.extend(self.scrape_jiji())
        
        # Remove duplicates (by URL)
        unique = []
        seen_urls = set()
        for listing in all_listings:
            if listing['url'] and listing['url'] not in seen_urls:
                seen_urls.add(listing['url'])
                unique.append(listing)
        
        logger.info(f"📊 TOTAL: {len(unique)} unique listings found")
        return unique
