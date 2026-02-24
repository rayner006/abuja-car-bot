import os
import logging
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
from scraper import CarScraper

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Get environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
APIFY_TOKEN = os.environ.get('APIFY_TOKEN')
WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL')

# Initialize scraper
scraper = CarScraper()

# ============================================
# Create a single event loop to reuse
# ============================================
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ============================================
# Define ALL handler functions FIRST
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued."""
    welcome_message = (
        "🚗 *Welcome to Abuja Car Finder Bot!*\n\n"
        "I help you find cars (Benz, Lexus, Toyota Venza/Avalon/Camry) "
        "from direct owners in Abuja.\n\n"
        "Available commands:\n"
        "/cars - Get latest car listings\n"
        "/distress - Get only distress sales\n"
        "/mercedes - Find Mercedes-Benz\n"
        "/lexus - Find Lexus\n"
        "/toyota - Find Toyota Venza/Avalon/Camry\n"
        "/help - Show this message\n\n"
        "Powered by Apify for reliable scraping! 🤖"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    await start(update, context)

async def get_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get latest car listings."""
    await update.message.reply_text("🔍 Searching for cars in Abuja... Please wait.")
    
    try:
        # Run scraper in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        listings = await loop.run_in_executor(
            None, 
            scraper.get_all_listings,
            True,  # use_apify
            10     # max_results
        )
        
        formatted_message = scraper.format_listings_for_telegram(listings)
        await update.message.reply_text(formatted_message, parse_mode='Markdown', disable_web_page_preview=False)
        
    except Exception as e:
        logger.error(f"Error in get_cars: {e}")
        await update.message.reply_text("Sorry, I encountered an error. Please try again later.")

async def get_distress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get only distress sales."""
    await update.message.reply_text("🔍 Searching for distress sales in Abuja... Please wait.")
    
    try:
        loop = asyncio.get_event_loop()
        all_listings = await loop.run_in_executor(
            None, 
            scraper.get_all_listings,
            True,  # use_apify
            20     # max_results
        )
        
        # Filter for distress sales
        distress_listings = [l for l in all_listings if l['is_distress']]
        
        if not distress_listings:
            await update.message.reply_text("No distress sales found at the moment.")
            return
        
        message = "🔴 *DISTRESS SALES IN ABUJA* 🔴\n\n"
        for i, listing in enumerate(distress_listings[:10], 1):
            message += f"{i}. *{listing['title']}*\n"
            message += f"💰 {listing['price']}\n"
            message += f"📍 {listing['location']}\n"
            message += f"[View]({listing['url']})\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Error in get_distress: {e}")
        await update.message.reply_text("Sorry, I encountered an error. Please try again later.")

async def get_mercedes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get Mercedes listings."""
    await filter_by_car_type(update, context, 'mercedes', '⭐ Mercedes-Benz')

async def get_lexus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get Lexus listings."""
    await filter_by_car_type(update, context, 'lexus', '✨ Lexus')

async def get_toyota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get Toyota listings."""
    await filter_by_car_type(update, context, 'toyota', '🌟 Toyota')

async def filter_by_car_type(update: Update, context: ContextTypes.DEFAULT_TYPE, car_type, display_name):
    """Filter listings by car type."""
    await update.message.reply_text(f"🔍 Searching for {display_name} in Abuja... Please wait.")
    
    try:
        loop = asyncio.get_event_loop()
        all_listings = await loop.run_in_executor(
            None, 
            scraper.get_all_listings,
            True,  # use_apify
            20     # max_results
        )
        
        # Filter for specific car type
        filtered = [l for l in all_listings if l['car_type'] == car_type]
        
        if not filtered:
            await update.message.reply_text(f"No {display_name} listings found at the moment.")
            return
        
        message = f"{display_name} *IN ABUJA*\n\n"
        for i, listing in enumerate(filtered[:10], 1):
            distress = "🔴 " if listing['is_distress'] else ""
            message += f"{distress}{i}. *{listing['title']}*\n"
            message += f"💰 {listing['price']}\n"
            message += f"📍 {listing['location']}\n"
            message += f"[View]({listing['url']})\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Error filtering by car type: {e}")
        await update.message.reply_text("Sorry, I encountered an error. Please try again later.")

# ============================================
# Initialize bot with the persistent loop
# ============================================

# Initialize bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)
loop.run_until_complete(bot.initialize())
logger.info("✅ Bot initialized successfully")

# ============================================
# Build application with the initialized bot
# ============================================

telegram_app = Application.builder().bot(bot).build()

# Add handlers (functions now exist)
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("cars", get_cars))
telegram_app.add_handler(CommandHandler("distress", get_distress))
telegram_app.add_handler(CommandHandler("mercedes", get_mercedes))
telegram_app.add_handler(CommandHandler("lexus", get_lexus))
telegram_app.add_handler(CommandHandler("toyota", get_toyota))

# Initialize application with the persistent loop
loop.run_until_complete(telegram_app.initialize())
logger.info("✅ Telegram application initialized successfully")

# ============================================
# Webhook and Routes
# ============================================

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint."""
    try:
        # Use the already initialized telegram_app with the persistent loop
        update = Update.de_json(request.get_json(force=True), bot)
        loop.run_until_complete(telegram_app.process_update(update))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "apify_configured": bool(APIFY_TOKEN),
        "telegram_configured": bool(TELEGRAM_BOT_TOKEN)
    }), 200

@app.route('/test-scraper', methods=['GET'])
def test_scraper():
    """Test endpoint for scraper (protected in production)."""
    try:
        listings = scraper.get_all_listings(use_apify=True, max_results=3)
        return jsonify({
            "success": True,
            "count": len(listings),
            "listings": listings
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint."""
    return "Abuja Car Bot is running! 🚗 Use Telegram to interact with me.", 200

if __name__ == '__main__':
    # Set up webhook using the persistent loop
    if WEBHOOK_URL and TELEGRAM_BOT_TOKEN:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        loop.run_until_complete(bot.set_webhook(url=webhook_url))
        logger.info(f"Webhook set to {webhook_url}")
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
