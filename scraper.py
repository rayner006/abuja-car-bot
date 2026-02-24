import os
import logging
import requests
from bs4 import BeautifulSoup
import time
import random
from fake_useragent import UserAgent
from datetime import datetime
from apify_client import ApifyClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CarScraper:
    def __init__(self):
        """Initialize the scraper with Apify client"""
        # Apify setup
        self.apify_token = os.environ.get('APIFY_TOKEN')
        if not self.apify_token:
            logger.warning("APIFY_TOKEN not found in environment variables")
        
        self.apify_client = ApifyClient(self.apify_token) if self.apify_token else None
        
        # Target car makes/models
        self.target_cars = {
            'mercedes': ['mercedes', 'benz', 'mercedes-benz', 'c-class', 'e-class'],
            'lexus': ['lexus', 'rx', 'rx350', 'rx330', 'es350', 'gs300'],
            'toyota': ['venza', 'avalon', 'camry', 'toyota venza', 'toyota avalon', 'toyota camry']
        }
        
        # Distress keywords
        self.distress_keywords = [
            'urgent sale', 'urgent', 'distress', 'distress sale', 'price drop',
            'must sell', 'leaving abroad', 'relocating', 'leaving nigeria',
            'travelling', 'visa approved', 'ready for bargain', 'best offer'
        ]
        
        # Backup Nairaland URL
        self.nairaland_url = "https://www.nairaland.com/cars"
        
        # User agent for backup scraper
        self.ua = UserAgent()
    
    def scrape_jiji_with_apify(self, max_results=10):
        """
        Scrape Jiji.ng using Apify's Jiji scraper
        Returns list of car listings
        """
        if not self.apify_client:
            logger.error("Apify client not initialized")
            return []
        
        listings = []
        
        try:
            # Prepare the actor input for Jiji scraper
            run_input = {
                "searchTerms": ["mercedes benz", "lexus", "toyota venza", "toyota avalon", "toyota camry"],
                "category": "cars",
                "location": "Abuja",
                "maxResults": max_results,
                "proxyConfiguration": {
                    "useApifyProxy": True,
                    "apifyProxyGroups": ["RESIDENTIAL"]
                }
            }
            
            logger.info(f"Starting Apify Jiji scraper")
            
            # Run the actor
            run = self.apify_client.actor("pocesar/jiji-scraper").call(run_input=run_input)
            
            # Fetch results from the dataset
            dataset_id = run["defaultDatasetId"]
            items = list(self.apify_client.dataset(dataset_id).iterate_items())
            
            logger.info(f"Retrieved {len(items)} items from Apify")
            
            # Process each item
            for item in items:
                listing = self._process_jiji_listing(item)
                if listing:
                    listings.append(listing)
                    
            logger.info(f"Processed {len(listings)} valid car listings from Jiji")
            
        except Exception as e:
            logger.error(f"Error scraping Jiji with Apify: {e}")
        
        return listings
    
    def _process_jiji_listing(self, item):
        """
        Process a single Jiji listing from Apify data
        Extract relevant information and check if it matches our criteria
        """
        try:
            # Extract basic info
            title = item.get('title', '')
            description = item.get('description', '')
            price = item.get('price', '')
            url = item.get('url', '')
            location = item.get('location', '')
            images = item.get('images', [])
            
            # Combine title and description for searching
            full_text = f"{title} {description}".lower()
            
            # Check if it's in Abuja
            if 'abuja' not in location.lower():
                return None
            
            # Check if it's one of our target cars
            car_type = self._identify_car_type(full_text)
            if not car_type:
                return None
            
            # Check if it's a distress sale
            is_distress = self._check_distress(full_text)
            
            # Format price
            formatted_price = self._format_price(price)
            
            # Get first image
            image_url = images[0] if images else None
            
            return {
                'title': title,
                'price': formatted_price,
                'url': url,
                'location': location,
                'car_type': car_type,
                'is_distress': is_distress,
                'image_url': image_url,
                'source': 'Jiji.ng (Apify)'
            }
            
        except Exception as e:
            logger.error(f"Error processing Jiji listing: {e}")
            return None
    
    def _identify_car_type(self, text):
        """Identify the type of car from the text"""
        text_lower = text.lower()
        
        for car_type, keywords in self.target_cars.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return car_type
        
        return None
    
    def _check_distress(self, text):
        """Check if the listing contains distress keywords"""
        text_lower = text.lower()
        
        for keyword in self.distress_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def _format_price(self, price_str):
        """Format price string"""
        if not price_str:
            return "Contact for price"
        
        # Clean and format price
        try:
            # Remove currency symbols and commas
            clean_price = price_str.replace('₦', '').replace(',', '').strip()
            if clean_price.isdigit():
                # Format with commas
                return f"₦{int(clean_price):,}"
        except:
            pass
        
        return price_str
    
    def scrape_nairaland_backup(self, max_pages=2):
        """
        Backup scraper for Nairaland
        Returns list of car listings
        """
        listings = []
        
        for page in range(1, max_pages + 1):
            try:
                # Construct URL with pagination
                if page == 1:
                    url = self.nairaland_url
                else:
                    url = f"{self.nairaland_url}/{page}"
                
                # Add random user agent
                headers = {
                    'User-Agent': self.ua.random
                }
                
                # Add delay to be respectful
                time.sleep(random.uniform(2, 4))
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all topic rows (Nairaland specific structure)
                topics = soup.find_all('tr', class_='topic_row')
                
                for topic in topics:
                    try:
                        # Extract title and link
                        title_link = topic.find('a', class_='topic_link')
                        if not title_link:
                            continue
                        
                        title = title_link.text.strip()
                        url = f"https://www.nairaland.com{title_link.get('href')}"
                        
                        # Check if it's about cars and in Abuja
                        full_text = title.lower()
                        
                        # Check for Abuja
                        if 'abuja' not in full_text:
                            continue
                        
                        # Check if it's one of our target cars
                        car_type = self._identify_car_type(full_text)
                        if not car_type:
                            continue
                        
                        # Check for distress
                        is_distress = self._check_distress(full_text)
                        
                        # Extract price (if mentioned in title)
                        price = self._extract_price_from_title(title)
                        
                        listings.append({
                            'title': title,
                            'price': price,
                            'url': url,
                            'location': 'Abuja',
                            'car_type': car_type,
                            'is_distress': is_distress,
                            'image_url': None,
                            'source': 'Nairaland'
                        })
                        
                    except Exception as e:
                        logger.error(f"Error parsing topic: {e}")
                        continue
                
                logger.info(f"Scraped page {page} of Nairaland, found {len(topics)} topics")
                
            except Exception as e:
                logger.error(f"Error scraping Nairaland page {page}: {e}")
        
        return listings
    
    def _extract_price_from_title(self, title):
        """Extract price from title if present"""
        import re
        
        # Look for price patterns like "1.5m", "1.5 million", "1,500,000"
        price_patterns = [
            r'₦?\s*(\d+(?:\.\d+)?)\s*(?:m|million|M)',
            r'₦?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:m|million|M)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                price_val = match.group(1).replace(',', '')
                if 'm' in pattern or 'million' in pattern.lower():
                    return f"₦{float(price_val):.1f}M"
                else:
                    return f"₦{price_val}"
        
        return "Price not specified"
    
    def get_all_listings(self, use_apify=True, max_results=10):
        """
        Get all car listings, primarily using Apify with Nairaland backup
        """
        all_listings = []
        
        # Try Apify first
        if use_apify and self.apify_client:
            logger.info("Attempting to scrape with Apify...")
            jiji_listings = self.scrape_jiji_with_apify(max_results)
            all_listings.extend(jiji_listings)
            
            # If Apify returns results, we're good
            if len(jiji_listings) >= max_results:
                logger.info(f"Found {len(jiji_listings)} listings from Apify")
                return all_listings[:max_results]
        
        # If Apify fails or returns few results, try Nairaland
        logger.info("Attempting backup scrape from Nairaland...")
        nairaland_listings = self.scrape_nairaland_backup(max_pages=2)
        all_listings.extend(nairaland_listings)
        
        # Sort by distress first, then by whatever
        all_listings.sort(key=lambda x: (-x['is_distress'], x['title']))
        
        return all_listings[:max_results]
    
    def format_listings_for_telegram(self, listings):
        """Format listings for Telegram message"""
        if not listings:
            return "No car listings found at the moment. Please try again later."
        
        message = "🚗 *Available Cars in Abuja*\n\n"
        
        for i, listing in enumerate(listings, 1):
            # Add distress indicator
            distress_badge = "🔴 *DISTRESS SALE* 🔴\n" if listing['is_distress'] else ""
            
            # Add car type emoji
            car_emoji = {
                'mercedes': '⭐',
                'lexus': '✨',
                'toyota': '🌟'
            }.get(listing['car_type'], '🚗')
            
            message += f"{distress_badge}{car_emoji} *{listing['title']}*\n"
            message += f"💰 *Price:* {listing['price']}\n"
            message += f"📍 *Location:* {listing['location']}\n"
            message += f"📱 *Source:* {listing['source']}\n"
            message += f"🔗 [View Listing]({listing['url']})\n"
            
            # Add image if available
            if listing.get('image_url'):
                message += f"[🖼️ Image]({listing['image_url']})\n"
            
            message += "─" * 30 + "\n\n"
        
        # Add timestamp
        message += f"🕐 *Last updated:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
