from flask import Flask, jsonify
import os
import threading
import time
import random
import logging
import requests
from datetime import datetime

# Import config and scraper
from config import *
from scraper import NigerianCarScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Track scan status
last_scan_time = None
last_results = []
scan_count = 0
cars_found_today = 0

# Initialize scraper
scraper = NigerianCarScraper()

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
            return True
        else:
            logger.error(f"Telegram error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Telegram: {e}")
        return False

def calculate_distress_score(text):
    """Calculate distress score based on keywords"""
    text_lower = text.lower()
    score = 0
    matched = []
    
    for keyword, weight in ALL_DISTRESS.items():
        if keyword in text_lower:
            score += weight
            matched.append(keyword)
    
    return score, matched

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
    
    # Format make icon
    make_icon = {
        'BENZ': '⭐',
        'LEXUS': '👑',
        'TOYOTA': '🚙'
    }.get(listing.get('make', ''), '🚗')
    
    # Format keywords found
    keywords_text = ", ".join(matched_keywords[:3]) if matched_keywords else ""
    
    message = (
        f"{emoji} {make_icon}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 <b>{listing.get('location', 'Abuja')}</b>\n"
        f"🚗 {listing.get('title', 'N/A')}\n"
        f"💰 {listing.get('price', 'Contact')}\n"
    )
    
    if keywords_text:
        message += f"⚠️ <i>{keywords_text}</i>\n"
    
    message += (
        f"📧 {listing.get('platform', 'Unknown')}\n"
        f"🔗 {listing.get('url', '#')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Found: {datetime.now().strftime('%H:%M:%S')}"
    )
    
    return message

def background_scraper():
    """Main scraping loop with REAL data"""
    global last_scan_time, last_results, scan_count, cars_found_today
    
    # Wait a bit for Flask to start
    time.sleep(5)
    
    # Send startup message
    startup_msg = (
        "🤖 <b>ABUJA CAR BOT STARTED!</b>\n\n"
        f"✅ Real scraping ACTIVE\n"
        f"📊 Scanning every {SCAN_INTERVAL_MINUTES} minutes\n"
        f"📍 Target: Abuja\n"
        f"🚗 Cars: Benz, Lexus, Toyota\n"
        f"🌐 Platforms: Jiji (Browser), Nairaland, OList\n"
        f"💰 Distress detection: ACTIVE\n\n"
        f"⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )
    send_telegram_message(startup_msg)
    logger.info("🤖 Bot started with BROWSER automation for Jiji!")
    
    while True:
        try:
            logger.info("🔍 Starting REAL scan cycle...")
            scan_start = datetime.now()
            scan_count += 1
            
            # Get REAL listings from scraper
            listings = scraper.scrape_all()
            
            new_found = 0
            for listing in listings:
                # Calculate distress score
                full_text = listing['title'] + " " + listing.get('description', '')
                distress_score, matched = calculate_distress_score(full_text)
                
                # Send to Telegram (with delay between messages)
                alert = format_car_alert(listing, distress_score, matched)
                send_telegram_message(alert)
                new_found += 1
                cars_found_today += 1
                time.sleep(2)  # Small delay between messages
            
            # Send summary
            scan_time = (datetime.now() - scan_start).total_seconds()
            summary = (
                f"📊 <b>Scan #{scan_count} Complete</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ Found: {new_found} new listings\n"
                f"📈 Today total: {cars_found_today}\n"
                f"⏱️ Scan took: {scan_time:.1f} seconds\n"
                f"🔄 Next scan: in {SCAN_INTERVAL_MINUTES} minutes"
            )
            send_telegram_message(summary)
            
            last_scan_time = datetime.now()
            last_results = listings
            logger.info(f"✅ Scan complete. Found {new_found} cars")
            
            # Wait for next scan (with random offset)
            next_run = (SCAN_INTERVAL_MINUTES * 60) + random.randint(0, 120)
            logger.info(f"Next scan in {next_run//60} min {next_run%60} sec")
            
            time.sleep(next_run)
            
        except Exception as e:
            logger.error(f"❌ Error in scraper: {e}")
            send_telegram_message(f"⚠️ Bot error: {str(e)[:200]}")
            time.sleep(300)  # Wait 5 min on error

@app.route('/')
def home():
    return jsonify({
        'status': 'alive',
        'service': 'Abuja Car Scraper Bot',
        'mode': 'BROWSER AUTOMATION',
        'telegram': 'Connected' if TELEGRAM_BOT_TOKEN else 'No token',
        'scan_count': scan_count,
        'cars_found_today': cars_found_today,
        'last_scan': last_scan_time.isoformat() if last_scan_time else 'Never',
        'next_scan': f'Every {SCAN_INTERVAL_MINUTES} minutes'
    })

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/test')
def test_telegram():
    """Test endpoint to send a message"""
    test_msg = (
        "🧪 <b>TEST MESSAGE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Bot is working with BROWSER mode!\n"
        f"📊 Scan count: {scan_count}\n"
        f"🚗 Cars found: {cars_found_today}\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    result = send_telegram_message(test_msg)
    if result:
        return jsonify({'status': 'Test message sent to Telegram'})
    else:
        return jsonify({'error': 'Failed to send'}), 500

@app.route('/scan')
def force_scan():
    """Force an immediate scan"""
    thread = threading.Thread(target=background_scraper)
    thread.start()
    return jsonify({'status': 'Scan started in background'})

if __name__ == '__main__':
    # Check Telegram credentials
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️ Telegram credentials not set!")
    else:
        logger.info("✅ Telegram credentials found")
    
    # Start background scraper
    thread = threading.Thread(target=background_scraper, daemon=True)
    thread.start()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
