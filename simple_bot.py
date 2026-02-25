#!/usr/bin/env python3
"""
Abuja Car Bot - Sends 8 cars every 30 min from your Apify dataset
Manually scrape Apify when dataset empty - bot tells you when!
AUTO-START - Runs forever once deployed
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

# How many cars to send per update
MAX_CARS_PER_MESSAGE = 8

# YOUR DATASET ID FROM APIFY CONSOLE
YOUR_DATASET_ID = "LbGDKcIwiRQilOepM"  # <-- 180 cars waiting here!

# File to remember which cars we've already sent
SENT_CARS_FILE = "sent_cars.json"

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

# ============================================
# APIFY FUNCTIONS - GET CARS FROM YOUR DATASET
# ============================================

def fetch_all_cars_from_dataset() -> List[Dict[str, Any]]:
    """Fetch ALL cars from your Apify dataset"""
    url = f"https://api.apify.com/v2/datasets/{YOUR_DATASET_ID}/items"
    params = {
        "token": APIFY_TOKEN,
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        cars = response.json()
        print(f"✅ Fetched {len(cars)} total cars from your dataset")
        return cars
    except Exception as e:
        print(f"❌ Error fetching cars: {e}")
        return []

def get_unsent_cars(all_cars: List[Dict[str, Any]], sent_cars: set) -> List[Dict[str, Any]]:
    """Return only cars that haven't been sent yet"""
    unsent = []
    for car in all_cars:
        # Use URL as unique identifier
        car_url = car.get('url', '')
        if car_url and car_url not in sent_cars:
            # Add analysis to car for sorting
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
    """Format cars with links and badges"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"🚗 *{title}*\n📅 {now}\n━━━━━━━━━━━━━━━━\n\n"
    
    for i, car in enumerate(cars, 1):
        title = car.get('title', 'Unknown Car')
        price = car.get('price', 'Price N/A')
        location = car.get('location', 'Abuja')
        url = car.get('url', '')
        analysis = car.get('analysis', analyze_listing(car))
        
        emoji, rating = get_deal_rating(analysis['deal_score'])
        badges = get_badges(analysis)
        
        message += f"{emoji} *{rating}* {emoji}\n"
        message += f"*{i}. {title}*\n"
        message += f"`{badges}`\n"
        message += f"💰 *Price:* {price}\n"
        message += f"📍 *Location:* {location}\n"
        
        if analysis['reasons']:
            message += f"💡 {analysis['reasons'][0]}\n"
        
        if url:
            message += f"🔗 [View Listing on Jiji]({url})\n"
        
        message += "─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n\n"
    
    # Add progress info
    if cars_left > 0:
        message += f"📊 *Sent {len(cars)} cars | {cars_left} remaining in dataset*"
    else:
        message += f"📊 *Sent {len(cars)} cars*"
    
    return message

# ============================================
# MAIN BOT LOGIC
# ============================================

def send_car_update():
    """Main function: Send 8 new cars from your dataset"""
    print(f"\n{'='*50}")
    print(f"🔍 Checking at {datetime.now()}")
    print(f"{'='*50}")
    
    # 1. Load which cars we've already sent
    sent_cars = load_sent_cars()
    print(f"📝 Already sent {len(sent_cars)} cars")
    
    # 2. Fetch ALL cars from your dataset
    all_cars = fetch_all_cars_from_dataset()
    
    if not all_cars:
        send_telegram_message("❌ Could not fetch cars from Apify. Check token or dataset ID.")
        return
    
    # 3. Get cars we haven't sent yet
    unsent_cars = get_unsent_cars(all_cars, sent_cars)
    
    # 4. Check if we have any cars left
    if not unsent_cars:
        message = (
            "⚠️ *DATASET COMPLETE* ⚠️\n\n"
            "✅ All 180 cars have been sent to Telegram!\n\n"
            "🔄 *Next step:*\n"
            "1. Go to Apify Console\n"
            "2. Run the Jiji scraper again\n"
            "3. Get new dataset ID\n"
            "4. Update YOUR_DATASET_ID in bot\n\n"
            "Bot will pause until new dataset is added."
        )
        send_telegram_message(message)
        print("🏁 All cars sent! Waiting for new dataset...")
        return
    
    # 5. Take next 8 cars
    next_cars = unsent_cars[:MAX_CARS_PER_MESSAGE]
    
    # 6. Mark these as sent
    for car in next_cars:
        car_url = car.get('url', '')
        if car_url:
            sent_cars.add(car_url)
    
    # 7. Save updated sent list
    save_sent_cars(sent_cars)
    
    # 8. Calculate remaining cars
    cars_remaining = len(unsent_cars) - len(next_cars)
    
    # 9. Format and send message
    if cars_remaining > 0:
        title = f"Next 8 Cars ({cars_remaining} remaining)"
    else:
        title = "Final 8 Cars in Dataset"
    
    message = format_car_message(next_cars, title, cars_remaining, len(all_cars))
    send_telegram_message(message)
    
    print(f"✅ Sent {len(next_cars)} cars. {cars_remaining} left in dataset")

def send_startup_message():
    """Send message when bot starts"""
    sent_cars = load_sent_cars()
    sent_count = len(sent_cars)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if sent_count == 0:
        status = "🆕 Fresh start - No cars sent yet"
    elif sent_count < 180:
        status = f"📊 Progress: {sent_count}/180 cars sent"
    else:
        status = "✅ All 180 cars sent - Ready for new dataset"
    
    message = (
        "🤖 *Abuja Car Bot Restarted*\n\n"
        f"🕐 {now}\n"
        f"{status}\n"
        "📡 Using YOUR dataset: LbGDKcIwiRQilOepM\n"
        "⏰ Sending 8 cars every 30 minutes\n\n"
        "_Updates starting soon..._"
    )
    send_telegram_message(message)

def run_continuous():
    """Run continuously - NO PROMPTS, AUTO-START"""
    print("""
    ╔════════════════════════════════╗
    ║    ABUJA CAR BOT - DEAL FINDER ║
    ║    AUTO-START - NO PROMPTS     ║
    ║    Sending 8 cars every 30 min ║
    ║    Dataset: 180 cars total     ║
    ╚════════════════════════════════╝
    """)
    
    # Send startup message
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
    # Verify environment variables
    missing = []
    if not APIFY_TOKEN: missing.append("APIFY_TOKEN")
    if not TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID: missing.append("TELEGRAM_CHAT_ID")
    
    if missing:
        print("❌ Missing:", ", ".join(missing))
        exit(1)
    
    # AUTO-START - NO PROMPTS!
    run_continuous()
