from flask import Flask, jsonify
import os
import threading
import time
import random
import logging
import requests
from datetime import datetime

# Import config
from config import *

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Track scan status
last_scan_time = None
last_results = []

def send_telegram_message(message):
    """Send message to your Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not set!")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ Telegram message sent")
            return True
        else:
            logger.error(f"❌ Telegram error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to send Telegram: {e}")
        return False

def calculate_distress_score(text):
    """Calculate distress score based on keywords"""
    text_lower = text.lower()
    score = 0
    matched = []
    
    for keyword, weight in DISTRESS_KEYWORDS.items():
        if keyword in text_lower:
            score += weight
            matched.append(keyword)
    
    return score, matched

def is_in_abuja(text):
    """Check if listing is in Abuja"""
    text_lower = text.lower()
    for area in ABUJA_AREAS:
        if area in text_lower:
            return True
    return False

def identify_make(title):
    """Identify if car is Benz, Lexus, or Toyota target"""
    title_lower = title.lower()
    
    for make, keywords in TARGET_MAKES.items():
        for keyword in keywords:
            if keyword in title_lower:
                return make
    return None

def send_test_message():
    """Send test message to confirm Telegram works"""
    message = (
        "🤖 <b>ABUJA CAR BOT IS ALIVE!</b>\n\n"
        f"✅ Bot started successfully\n"
        f"📊 Scanning every {SCAN_INTERVAL_MINUTES} minutes\n"
        f"📍 Target: Abuja\n"
        f"🚗 Cars: Benz, Lexus, Toyota (Venza/Avalon/Camry)\n"
        f"💰 Distress keywords active\n\n"
        f"⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )
    return send_telegram_message(message)

def scrape_simulation():
    """Simulated scraping - will be replaced with real scraper"""
    test_listings = [
        {
            'title': 'URGENT: Mercedes Benz C300 2018 Abuja',
            'price': '₦14,500,000',
            'location': 'Wuse 2, Abuja',
            'url': 'https://jiji.ng/test1',
            'platform': 'Jiji.ng',
            'description': 'Distress sale! Relocating abroad, need cash urgently'
        },
        {
            'title': 'Lexus RX350 2016 for quick sale',
            'price': '₦8,200,000',
            'location': 'Maitama, Abuja',
            'url': 'https://nairaland.com/test2',
            'platform': 'Nairaland',
            'description': 'Price crash! Below market value'
        },
        {
            'title': 'Toyota Camry 2019 - Urgent Sale',
            'price': '₦4,500,000',
            'location': 'Gwarinpa, Abuja',
            'url': 'https://olist.ng/test3',
            'platform': 'OList.ng',
            'description': 'Need cash urgently, price negotiable'
        }
    ]
    return test_listings

def format_car_alert(listing, distress_score, matched_keywords):
    """Format car listing for Telegram"""
    
    # Determine alert emoji based on score
    if distress_score >= 7:
        emoji = "🔥🔥 EXTREME DISTRESS!"
    elif distress_score >= 5:
        emoji = "🔥 HOT DISTRESS"
    elif distress_score >= 3:
        emoji = "💰 GOOD DEAL"
    else:
        emoji = "🚗 NEW LISTING"
    
    # Format keywords found
    keywords_text = ", ".join(matched_keywords[:3]) if matched_keywords else "None"
    
    message = (
        f"{emoji}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>{listing.get('location', 'Abuja')}</b>\n"
        f"🚗 <b>{listing.get('title', 'N/A')}</b>\n"
        f"💰 {listing.get('price', 'Contact for price')}\n"
    )
    
    if matched_keywords:
        message += f"⚠️ Distress: {keywords_text}\n"
    
    message += (
        f"🌐 {listing.get('platform', 'Unknown')}\n"
        f"🔗 {listing.get('url', '#')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ Found: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    return message

def background_scraper():
    """Main scraping loop"""
    global last_scan_time, last_results
    
    # Wait a bit for Flask to start
    time.sleep(5)
    
    # Send startup message
    send_test_message()
    logger.info("🤖 Bot started - test message sent to Telegram")
    
    while True:
        try:
            logger.info("🔍 Starting scan cycle...")
            scan_start = datetime.now()
            
            # SIMULATION MODE - Will replace with real scraping
            listings = scrape_simulation()
            
            new_found = 0
            for listing in listings:
                # Calculate distress score
                full_text = listing['title'] + " " + listing.get('description', '')
                distress_score, matched = calculate_distress_score(full_text)
                
                # Check location and make
                if is_in_abuja(full_text) or is_in_abuja(listing['location']):
                    make = identify_make(listing['title'])
                    if make:
                        # Send to Telegram
                        alert = format_car_alert(listing, distress_score, matched)
                        send_telegram_message(alert)
                        new_found += 1
                        time.sleep(2)  # Small delay between messages
            
            # Send summary
            scan_time = (datetime.now() - scan_start).total_seconds()
            summary = (
                f"📊 <b>Scan Complete</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ Found: {new_found} new listings\n"
                f"⏱️ Scan took: {scan_time:.1f} seconds\n"
                f"🔄 Next scan: in {SCAN_INTERVAL_MINUTES} minutes"
            )
            send_telegram_message(summary)
            
            last_scan_time = datetime.now()
            logger.info(f"✅ Scan complete. Found {new_found} new cars")
            
            # Wait for next scan (with random offset)
            next_run = (SCAN_INTERVAL_MINUTES * 60) + random.randint(0, 120)
            logger.info(f"Next scan in {next_run//60} min {next_run%60} sec")
            
            time.sleep(next_run)
            
        except Exception as e:
            logger.error(f"❌ Error in scraper: {e}")
            send_telegram_message(f"⚠️ Bot error: {str(e)[:100]}")
            time.sleep(300)  # Wait 5 min on error

@app.route('/')
def home():
    return jsonify({
        'status': 'alive',
        'service': 'Abuja Car Scraper Bot',
        'telegram': 'Connected' if TELEGRAM_BOT_TOKEN else 'No token',
        'last_scan': last_scan_time.isoformat() if last_scan_time else 'Never',
        'next_scan': f'Every {SCAN_INTERVAL_MINUTES} minutes'
    })

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/test')
def test_telegram():
    """Test endpoint to send a message"""
    result = send_test_message()
    if result:
        return jsonify({'status': 'Test message sent to Telegram'})
    else:
        return jsonify({'error': 'Failed to send'}), 500

if __name__ == '__main__':
    # Check Telegram credentials
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set!")
        logger.warning("Add them in Render Environment Variables")
    else:
        logger.info("✅ Telegram credentials found")
    
    # Start background scraper
    thread = threading.Thread(target=background_scraper, daemon=True)
    thread.start()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
