#!/usr/bin/env python3
"""
Abuja Car Bot - Sends 8 Abuja cars every 30 min from your Apify dataset
With complete Abuja locations and working links!
"""

import os
import time
import json
import requests
import schedule
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path

# ============================================
# CONFIGURATION - Get from environment variables
# ============================================
APIFY_TOKEN = os.environ.get('APIFY_TOKEN')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Dataset ID from environment (you set this as DATASET_ID in Render)
APIFY_DATASET_ID = os.environ.get('DATASET_ID')

# How many cars to send per update
MAX_CARS_PER_MESSAGE = 8

# File to remember which cars we've already sent
SENT_CARS_FILE = "sent_cars.json"

# ============================================
# VERIFY ALL ENVIRONMENT VARIABLES
# ============================================
missing = []
if not APIFY_TOKEN: missing.append("APIFY_TOKEN")
if not TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_CHAT_ID: missing.append("TELEGRAM_CHAT_ID")
if not APIFY_DATASET_ID: missing.append("DATASET_ID (set as APIFY_DATASET_ID in code)")

if missing:
    print("❌ Missing required environment variables:", ", ".join(missing))
    print("Please set these in your Render dashboard.")
    exit(1)

print(f"✅ Using Dataset ID: {APIFY_DATASET_ID}")

# ============================================
# MEMORY FUNCTIONS - Track sent cars
# ============================================

def load_sent_cars() -> set:
    """Load the list of car URLs we've already sent"""
    try:
        if Path(SENT_CARS_FILE).exists():
            with open(SENT_CARS_FILE, 'r') as f:
                return set(json.load(f))
        else:
            print("📝 No sent cars file found, starting fresh")
            return set()
    except Exception as e:
        print(f"⚠️ Could not load sent cars: {e}")
        return set()

def save_sent_cars(sent_cars: set):
    """Save the list of sent car URLs"""
    try:
        with open(SENT_CARS_FILE, 'w') as f:
            json.dump(list(sent_cars), f)
        print(f"✅ Saved {len(sent_cars)} sent cars to memory")
    except Exception as e:
        print(f"⚠️ Could not save sent cars: {e}")

# ============================================
# COMPLETE ABUJA LOCATIONS - ALL AREAS!
# ============================================

def filter_abuja_only(cars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter cars to show only Abuja/FCT results - EVERYWHERE!
    From the big mansions to the small streets!
    """
    # 🔴 COMPLETE ABUJA/FCT LOCATIONS
    abuja_keywords = [
        # Main city areas
        'abuja', 'fct', 'f.c.t', 'federal capital territory',
        
        # PHASE 1 - Central areas
        'central area', 'phase 1', 'phase i', 'garki', 'garki i', 'garki ii',
        'wuse', 'wuse i', 'wuse ii', 'wuse zone', 'asokoro', 'maitama',
        'jabi', 'jabi airport', 'jabi road', 'utako', 'guzape', 'durumi',
        
        # PHASE 2 - Extensions
        'phase 2', 'phase ii', 'wuye', 'katampe', 'kado', 'kado estate',
        'life camp', 'lifecamp', 'life camp estate',
        'mabushi', 'mabushi district',
        
        # PHASE 3 - Developing areas
        'phase 3', 'phase iii', 'iwo road', 'nyanya', 'karu', 'karu site',
        'gwagwalada', 'kubwa', 'kubwa expressway', 'bwari', 'bwari area',
        'dutse', 'dutse abuja',
        
        # Satellite towns
        'lugbe', 'lugbe abuja', 'lugbe airport', 'karshi',
        'nyanya', 'nyanya karu', 'nyanya market',
        'mararaba', 'mararaba abuja', 'masaka',
        
        # Major roads & districts
        'airport road', 'abuja airport road', 'mbora',
        'gwarimpa', 'gwarinpa', 'gwarinpa estate',
        'dawaki', 'dawaki abuja', 'dawaki extension',
        'kubwa', 'kubwa phase', 'kubwa extension',
        
        # Eastern bypass areas
        'apo', 'apo legislative', 'apo zone', 'apo district',
        'apo resettlement', 'gudu', 'gudu district',
        
        # Other FCT areas
        'zuba', 'zuba abuja', 'dei dei', 'kuje', 'kwali', 'abaji',
        
        # Estates & neighborhoods
        'sunny vale', 'sunnyvale', 'sunny vale estate',
        'apex estate', 'prince and princess', 'princess estate',
        'efab', 'efab estate', 'trademore', 'trademore estate',
        'love garden', 'love garden estate',
        
        # All phases and zones
        'phase 4', 'phase iv', 'phase 5', 'phase v',
        'zone 1', 'zone 2', 'zone 3', 'zone 4', 'zone e', 'zone f', 'zone g',
        
        # Street-level (common mentions)
        'constituency road', 'constitution road', 'shehu shagari way',
        'ahmadu bello way', 'murtala mohammed way', 'moshood abiola way',
        
        # Area numbers
        'area 1', 'area 2', 'area 3', 'area 4', 'area 5', 'area 6', 'area 7',
        'area 8', 'area 9', 'area 10', 'area 11', 'area 12', 'area 13',
        'area 14', 'area 15',
        
        # Near airports
        'nnamdi azikiwe airport', 'abuja airport', 'airport village',
        
        # Institutions (people dey use as landmarks)
        'university of abuja', 'uniabuja', 'baze university',
        'veritas university', 'nile university',
        'american international school', 'army barracks',
        
        # Markets
        'wuse market', 'garki market', 'gwarinpa market',
        'kubwa market', 'nyanya market', 'karu market',
        'utako market', 'jabi lake', 'jabi park',
        'millennium park', 'city park',
        
        # New developments
        'katampe extension', 'cbd', 'central business district',
        'diplomatic zone', 'diplomatic drive',
        'presidential quarters', 'presidential villa',
        
        # Area councils
        'abaji area', 'bwari area', 'gwagwalada area',
        'kuje area', 'kwali area', 'municipal area',
        
        # Local lingo
        'town', 'buja', 'the capital', 'fct abuja', 'abuja city',
        'city center', 'main city',
    ]
    
    filtered_cars = []
    print("\n📍 FILTERING FOR ABUJA CARS...")
    
    for car in cars:
        # Check all possible location fields
        location_fields = [
            str(car.get('region_name', '')).lower(),
            str(car.get('region', '')).lower(),
            str(car.get('location', '')).lower(),
            str(car.get('address', '')).lower(),
            str(car.get('area', '')).lower(),
            str(car.get('zone', '')).lower(),
            str(car.get('district', '')).lower(),
        ]
        
        # Also check title and description for location hints
        title = str(car.get('title', '')).lower()
        description = str(car.get('short_description', '') or car.get('details', '')).lower()
        
        full_location_text = ' '.join(location_fields) + ' ' + title + ' ' + description
        
        # Check if any Abuja keyword dey
        is_abuja = any(keyword in full_location_text for keyword in abuja_keywords)
        
        if is_abuja:
            filtered_cars.append(car)
            print(f"✅ Abuja: {car.get('title', 'No title')[:40]}...")
        else:
            # Skip non-Abuja cars
            pass
    
    print(f"📊 Abuja cars found: {len(filtered_cars)} out of {len(cars)} total")
    return filtered_cars

# ============================================
# NIGERIAN CAR MARKET KEYWORDS
# ============================================

DIRECT_SELLER_KEYWORDS = [
    'direct owner', 'owner selling', 'personal use', 'personal car',
    'direct from owner', 'one owner', 'first owner', 'private seller',
    'not a dealer', 'no agents', 'no brokers', 'sell by owner',
    'owner direct', 'genuine owner', 'myself selling', 'i am selling',
    'my personal', 'i sell', 'owner dealing', 'physically here',
    'you can come', 'come see', 'inspection welcome', 'see and buy',
    'my car', 'i dey sell', 'person dey sell', 'owner dey'
]

USED_CAR_KEYWORDS = [
    'used', 'tokunbo', 'fairly used', 'second hand', 'pre-owned',
    'locally used', 'foreign used', 'uk used', 'usa used',
    'europe used', 'clean used', 'used condition', 'original used',
    'nigeria used', 'abuja used', 'lagos used', 'cleared',
    'duty paid', 'custom cleared', 'tokunbo car', 'foreign used'
]

CHEAP_KEYWORDS = [
    'cheap', 'affordable', 'bargain', 'low price', 'best price',
    'price drop', 'reduced', 'negotiable', 'make offer',
    'budget', 'economical', 'wallet friendly', 'cheapest',
    'neg', 'price neg', 'negotiable', 'haggle',
    'best offer', 'serious buyer', 'cash price', 'good price',
    'give away', 'giveaway', 'below market', 'fair price'
]

DISTRESS_KEYWORDS = [
    'urgent sale', 'urgent', 'distress', 'distress sale',
    'must sell', 'need to sell', 'forced sale', 'quick sale',
    'relocating', 'relocation', 'leaving abroad', 'traveling',
    'travelling', 'moving abroad', 'leaving nigeria', 'visa approved',
    'greencard', 'greencard approved', 'moving overseas', 'emigrating',
    'japa', 'need cash', 'quick cash', 'emergency', 'urgent cash',
    'financial', 'school fees', 'project money', 'business capital',
    'medical', 'hospital', 'need money', 'cash urgent',
    'price crash', 'sacrifice', 'clearance', 'last price',
    'take over', 'ready to go', 'must go', 'price slashed',
    'slashed', 'cut price', 'give away price'
]

PIDGIN_KEYWORDS = [
    'dey sell', 'owner dey', 'direct owner dey', 'person dey sell',
    'my car', 'i dey sell', 'make offer', 'we dey negotiate',
    'last last', 'final price', 'cash carry', 'come see',
    'walahi', 'original', 'clean car', 'mint condition',
    'baby use', 'carefully used', 'adult driven'
]

# ============================================
# CAR ANALYSIS FUNCTIONS
# ============================================

def analyze_listing(car: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a car listing and return all relevant flags"""
    title = str(car.get('title', '')).lower()
    description = str(car.get('short_description', '') or car.get('details', '') or '').lower()
    full_text = f"{title} {description}"
    
    is_direct_seller = any(keyword in full_text for keyword in DIRECT_SELLER_KEYWORDS + PIDGIN_KEYWORDS)
    is_used = any(keyword in full_text for keyword in USED_CAR_KEYWORDS)
    is_cheap = any(keyword in full_text for keyword in CHEAP_KEYWORDS)
    is_distress = any(keyword in full_text for keyword in DISTRESS_KEYWORDS)
    
    deal_score = 0
    reasons = []
    
    if is_direct_seller:
        deal_score += 3
        reasons.append("👤 Direct Owner")
    if is_used:
        deal_score += 1
        reasons.append("🔧 Used Car")
    if is_cheap:
        deal_score += 2
        reasons.append("💰 Cheap Price")
    if is_distress:
        deal_score += 3
        reasons.append("🆘 Distress Sale")
    
    if is_direct_seller and is_distress:
        deal_score += 2
        reasons.append("✨ Owner in distress - BEST DEAL!")
    if is_used and is_cheap:
        deal_score += 1
        reasons.append("👍 Great value used car")
    
    return {
        'is_direct_seller': is_direct_seller,
        'is_used': is_used,
        'is_cheap': is_cheap,
        'is_distress': is_distress,
        'deal_score': min(deal_score, 10),
        'reasons': reasons[:2]
    }

def get_deal_rating(score: int) -> Tuple[str, str]:
    """Convert score to emoji rating"""
    if score >= 8:
        return "🔥🔥", "HOT DEAL"
    elif score >= 5:
        return "🔥", "GREAT FIND"
    elif score >= 3:
        return "✨", "Good Deal"
    else:
        return "📌", "Regular Listing"

def get_badges(analysis: Dict[str, Any]) -> str:
    """Create badge string"""
    badges = []
    if analysis['is_direct_seller']:
        badges.append("👤 DIRECT")
    if analysis['is_used']:
        badges.append("🔧 USED")
    if analysis['is_cheap']:
        badges.append("💰 CHEAP")
    if analysis['is_distress']:
        badges.append("🆘 DISTRESS")
    
    return " | ".join(badges) if badges else "📋 REGULAR"

def filter_best_deals(cars: List[Dict[str, Any]], min_score: int = 5) -> List[Dict[str, Any]]:
    """Return only cars with good deal scores"""
    good_deals = []
    for car in cars:
        analysis = analyze_listing(car)
        if analysis['deal_score'] >= min_score:
            car['analysis'] = analysis
            good_deals.append(car)
    return good_deals

# ============================================
# APIFY FUNCTIONS - Fetch from your dataset
# ============================================

def fetch_all_cars_from_dataset() -> List[Dict[str, Any]]:
    """Fetch ALL cars from your Apify dataset"""
    url = f"https://api.apify.com/v2/datasets/{APIFY_DATASET_ID}/items"
    params = {
        "token": APIFY_TOKEN,
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        cars = response.json()
        print(f"✅ Fetched {len(cars)} total cars from dataset")
        return cars
    except Exception as e:
        print(f"❌ Error fetching cars: {e}")
        return []

def get_unsent_cars(all_cars: List[Dict[str, Any]], sent_cars: set) -> List[Dict[str, Any]]:
    """Return only cars that haven't been sent yet"""
    unsent = []
    for car in all_cars:
        # Try multiple possible URL fields
        car_url = (car.get('url') or car.get('message_url') or car.get('guid') or '')
        if car_url and car_url not in sent_cars:
            car['analysis'] = analyze_listing(car)
            unsent.append(car)
    
    # Sort by deal score (best deals first)
    unsent.sort(key=lambda x: x['analysis']['deal_score'], reverse=True)
    
    print(f"📊 Unsent cars: {len(unsent)} out of {len(all_cars)} total")
    return unsent

# ============================================
# TELEGRAM FUNCTIONS
# ============================================

def send_telegram_message(text: str, parse_mode: str = "Markdown") -> bool:
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Message sent to Telegram")
        return True
    except Exception as e:
        print(f"❌ Failed to send: {e}")
        return False

def format_car_message(cars: List[Dict[str, Any]], title: str = "Abuja Cars Update", 
                       cars_left: int = 0, total_cars: int = 0) -> str:
    """Format cars with links and badges - WITH JIJI DOMAIN FIX"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"🚗 *{title}*\n📅 {now}\n━━━━━━━━━━━━━━━━\n\n"
    
    for i, car in enumerate(cars, 1):
        # Get basic info
        car_title = car.get('title', 'Unknown Car')
        
        # Price handling
        price_obj = car.get('price_obj', {})
        if isinstance(price_obj, dict):
            price = price_obj.get('N', '') or price_obj.get('value', '') or 'Price N/A'
        else:
            price = car.get('price_title', 'Price N/A')
        
        # Location
        location = (car.get('region_name', '') or car.get('region', '') or 
                   car.get('location', '') or 'Abuja')
        
        # 🔗 URL FIX - Add Jiji domain if needed
        url_path = (car.get('url') or car.get('message_url') or car.get('guid') or '')
        
        if url_path:
            if url_path.startswith('/'):
                full_url = f"https://jiji.ng{url_path}"
            elif not url_path.startswith('http'):
                full_url = f"https://{url_path}"
            else:
                full_url = url_path
        else:
            full_url = ''
        
        # Get analysis
        analysis = car.get('analysis', analyze_listing(car))
        emoji, rating = get_deal_rating(analysis['deal_score'])
        badges = get_badges(analysis)
        
        # Build message
        message += f"{emoji} *{rating}* {emoji}\n"
        message += f"*{i}. {car_title}*\n"
        message += f"`{badges}`\n"
        message += f"💰 *Price:* {price}\n"
        message += f"📍 *Location:* {location}\n"
        
        if analysis['reasons']:
            message += f"💡 {analysis['reasons'][0]}\n"
        
        # Add link if available
        if full_url:
            message += f"🔗 [View Listing on Jiji]({full_url})\n"
        
        message += "─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n\n"
    
    # Add summary
    if cars_left > 0:
        message += f"📊 *Sent {len(cars)} cars | {cars_left} remaining in Abuja*"
    else:
        message += f"📊 *Sent {len(cars)} cars*"
    
    return message

# ============================================
# MAIN BOT LOGIC
# ============================================

def send_car_update():
    """Main function: Send 8 new Abuja cars from your dataset"""
    print(f"\n{'='*50}")
    print(f"🔍 Checking at {datetime.now()}")
    print(f"{'='*50}")
    
    # Load sent cars
    sent_cars = load_sent_cars()
    print(f"📝 Already sent {len(sent_cars)} cars")
    
    # Fetch all cars
    all_cars = fetch_all_cars_from_dataset()
    
    if not all_cars:
        send_telegram_message("❌ Could not fetch cars from Apify. Check token or dataset ID.")
        return
    
    # Filter for Abuja only
    abuja_cars = filter_abuja_only(all_cars)
    
    # Get unsent Abuja cars
    unsent_cars = get_unsent_cars(abuja_cars, sent_cars)
    
    # Check if any unsent cars left
    if not unsent_cars:
        if len(abuja_cars) == 0:
            message = (
                "⚠️ *NO ABUJA CARS FOUND* ⚠️\n\n"
                f"✅ Dataset has {len(all_cars)} cars total\n"
                "❌ But none for Abuja/FCT\n\n"
                "🔄 *Next step:*\n"
                "1. Run Jiji scraper again\n"
                "2. Target Abuja specifically"
            )
        else:
            message = (
                "⚠️ *DATASET COMPLETE* ⚠️\n\n"
                f"✅ All {len(abuja_cars)} Abuja cars have been sent!\n"
                f"📊 Total in dataset: {len(all_cars)} cars\n\n"
                "🔄 *Next step:*\n"
                "1. Go to Apify Console\n"
                "2. Run the Jiji scraper again\n"
                "3. Update DATASET_ID in Render\n\n"
                "Bot will pause until new dataset is added."
            )
        send_telegram_message(message)
        print("🏁 All Abuja cars sent! Waiting for new dataset...")
        return
    
    # Take next 8 cars
    next_items = unsent_cars[:MAX_CARS_PER_MESSAGE]
    
    # Mark as sent
    for item in next_items:
        item_url = (item.get('url') or item.get('message_url') or item.get('guid') or '')
        if item_url:
            sent_cars.add(item_url)
    
    # Save sent cars
    save_sent_cars(sent_cars)
    
    # Calculate remaining
    items_remaining = len(unsent_cars) - len(next_items)
    
    # Format and send message
    title = f"Next {len(next_items)} Abuja Cars ({items_remaining} Abuja remaining)"
    message = format_car_message(next_items, title, items_remaining, len(abuja_cars))
    send_telegram_message(message)
    
    print(f"✅ Sent {len(next_items)} Abuja cars. {items_remaining} Abuja cars left")

def send_startup_message():
    """Send message when bot starts"""
    sent_cars = load_sent_cars()
    sent_count = len(sent_cars)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    message = (
        "🤖 *Abuja Car Bot Restarted*\n\n"
        f"🕐 {now}\n"
        f"📡 Dataset: `{APIFY_DATASET_ID[:8]}...`\n"
        f"📍 *Filter:* Abuja/FCT only 🇳🇬\n"
        f"📊 Progress: {sent_count} Abuja cars sent so far\n"
        "⏰ Sending 8 Abuja cars every 30 minutes\n\n"
        "_Updates starting soon..._"
    )
    send_telegram_message(message)

def run_continuous():
    """Run continuously - NO PROMPTS, AUTO-START"""
    print("""
    ╔════════════════════════════════╗
    ║    ABUJA CAR BOT - FINAL VERSION ║
    ║    AUTO-START - NO PROMPTS     ║
    ║    Sending 8 Abuja cars every 30 min║
    ╚════════════════════════════════╝
    """)
    print(f"📡 Dataset ID: {APIFY_DATASET_ID}")
    
    try:
        send_startup_message()
    except Exception as e:
        print(f"⚠️ Could not send startup message: {e}")
    
    # Run immediately
    send_car_update()
    
    # Schedule regular checks
    schedule.every(30).minutes.do(send_car_update)
    
    # Keep running forever
    print("📡 Bot is running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        try:
            send_telegram_message("🛑 Bot stopped")
        except:
            pass

# ============================================
# ENTRY POINT - AUTO-START
# ============================================

if __name__ == "__main__":
    run_continuous()
