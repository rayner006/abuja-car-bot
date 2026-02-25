#!/usr/bin/env python3
"""
Abuja Car Bot - Automatically sends Jiji.ng car deals to Telegram every 30 minutes
Finds direct sellers, used cars, cheap prices, and distress sales
"""

import os
import time
import requests
import schedule
from datetime import datetime
from typing import List, Dict, Any, Tuple

# ============================================
# CONFIGURATION - Get from environment variables
# ============================================
APIFY_TOKEN = os.environ.get('APIFY_TOKEN')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# How many cars to send per update
MAX_CARS_PER_MESSAGE = 8

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
    description = str(car.get('description', '')).lower()
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
# APIFY FUNCTIONS
# ============================================

def get_latest_dataset_id() -> str:
    """Find the most recent dataset ID from Apify"""
    url = "https://api.apify.com/v2/datasets"
    params = {
        "token": APIFY_TOKEN,
        "limit": 1,
        "desc": True
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    datasets = data.get('data', [])
    
    if not datasets:
        raise Exception("No datasets found")
    
    latest = datasets[0]
    dataset_id = latest['id']
    item_count = latest.get('itemCount', 0)
    created_at = latest.get('createdAt', 'unknown')
    
    print(f"📊 Latest dataset: {dataset_id} ({item_count} items, {created_at})")
    
    return dataset_id

def fetch_cars_from_dataset(dataset_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch car listings from Apify dataset"""
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    params = {
        "token": APIFY_TOKEN,
        "limit": limit,
        "format": "json"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    cars = response.json()
    print(f"✅ Fetched {len(cars)} cars")
    
    return cars

def check_for_new_scrape() -> List[Dict[str, Any]]:
    """Check for new scrape and get data"""
    try:
        dataset_id = get_latest_dataset_id()
        cars = fetch_cars_from_dataset(dataset_id, limit=MAX_CARS_PER_MESSAGE * 2)
        return cars
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

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
        "disable_web_page_preview": False  # This enables link previews!
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Message sent to Telegram")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def format_car_message(cars: List[Dict[str, Any]], title: str = "Abuja Cars Update") -> str:
    """Format cars with links and badges"""
    if not cars:
        return "No cars found in the latest scrape."
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"🚗 *{title}*\n📅 {now}\n━━━━━━━━━━━━━━━━\n\n"
    
    for i, car in enumerate(cars[:MAX_CARS_PER_MESSAGE], 1):
        title = car.get('title', 'Unknown Car')
        price = car.get('price', 'Price N/A')
        location = car.get('location', 'Abuja')
        url = car.get('url', '')
        
        analysis = analyze_listing(car)
        emoji, rating = get_deal_rating(analysis['deal_score'])
        badges = get_badges(analysis)
        
        message += f"{emoji} *{rating}* {emoji}\n"
        message += f"*{i}. {title}*\n"
        message += f"`{badges}`\n"
        message += f"💰 *Price:* {price}\n"
        message += f"📍 *Location:* {location}\n"
        
        if analysis['reasons']:
            message += f"💡 {analysis['reasons'][0]}\n"
        
        # THIS IS THE LINK YOU WANT - CLICKABLE!
        if url:
            message += f"🔗 [View Listing on Jiji]({url})\n"
        
        message += "─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n\n"
    
    hot_deals = sum(1 for car in cars if analyze_listing(car)['deal_score'] >= 5)
    message += f"📊 *{len(cars[:MAX_CARS_PER_MESSAGE])} cars shown"
    if hot_deals > 0:
        message += f" | 🔥 {hot_deals} hot deals"
    message += "*\n🤖 *Updates every 30 min*"
    
    return message

# ============================================
# MAIN BOT LOGIC
# ============================================

def send_car_update():
    """Main function: Check and send cars"""
    print(f"\n{'='*50}")
    print(f"🔍 Checking at {datetime.now()}")
    print(f"{'='*50}")
    
    cars = check_for_new_scrape()
    
    if not cars:
        print("ℹ️ No cars found")
        return
    
    # Send regular update
    regular_message = format_car_message(cars, "Latest Cars in Abuja")
    send_telegram_message(regular_message)
    
    # Send hot deals separately
    best_deals = filter_best_deals(cars, min_score=5)
    if best_deals:
        print(f"🔥 Found {len(best_deals)} hot deals!")
        deals_message = format_car_message(best_deals, "🔥 HOT DEALS ALERT! 🔥")
        send_telegram_message(deals_message)
    
    time.sleep(2)

def send_startup_message():
    """Send message when bot starts"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = (
        "🤖 *Abuja Car Bot Started*\n\n"
        f"🕐 {now}\n"
        "📡 Monitoring Apify for new cars\n"
        "⏰ Updates every 30 minutes\n\n"
        "*I'll send:*\n"
        "• Latest cars with 🔗 links to Jiji\n"
        "• 🔥 Hot deal alerts\n"
        "• Direct seller & distress badges\n\n"
        "_First update coming in a few seconds..._"
    )
    send_telegram_message(message)

def run_once():
    """Run once for testing"""
    print("🚀 Running one-time check...")
    send_car_update()
    print("✅ Done!")

def run_scheduler():
    """Run continuously"""
    print("🚀 Starting Abuja Car Bot")
    print("📡 Checking every 30 minutes")
    print("Press Ctrl+C to stop\n")
    
    send_startup_message()
    send_car_update()  # Run immediately
    
    schedule.every(30).minutes.do(send_car_update)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
        send_telegram_message("🛑 Bot stopped")

# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    # Verify environment variables
    missing = []
    if not APIFY_TOKEN: missing.append("APIFY_TOKEN")
    if not TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID: missing.append("TELEGRAM_CHAT_ID")
    
    if missing:
        print("❌ Missing:", ", ".join(missing))
        exit(1)
    
    print("""
    ╔════════════════════════════════╗
    ║    ABUJA CAR BOT - DEAL FINDER ║
    ║    Sends links every 30 min    ║
    ╚════════════════════════════════╝
    """)
    
    print("1. Run once (test)")
    print("2. Run continuously (recommended)")
    
    choice = input("Choose (1 or 2): ").strip()
    
    if choice == "1":
        run_once()
    else:
        run_scheduler()
