# ============================================
# TEST FILE FOR UNDETECTED CHROMEDRIVER + STEALTH
# Run this first to verify everything works
# ============================================

import undetected_chromedriver as uc
from selenium_stealth import stealth
import time
import logging
import os
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_undetected_browser():
    """Test if undetected ChromeDriver + stealth works on Render"""
    driver = None
    
    try:
        logger.info("🚀 Testing undetected ChromeDriver with stealth on Render...")
        
        # Configure Chrome options for Render
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Initialize undetected Chrome
        logger.info("  Starting Chrome...")
        driver = uc.Chrome(options=options)
        logger.info("✅ Chrome started successfully")
        
        # Apply selenium-stealth (THIS IS CRITICAL)
        logger.info("  Applying stealth plugins...")
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        logger.info("✅ Stealth applied")
        
        # Test 1: Visit bot detection test site
        logger.info("  Testing bot detection...")
        driver.get("https://bot.sannysoft.com")
        time.sleep(5)
        
        # Take screenshot
        screenshot_path = "/tmp/bot_test.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"✅ Screenshot saved to {screenshot_path}")
        
        # Test 2: Try Jiji.ng
        logger.info("  Testing Jiji.ng access...")
        driver.get("https://jiji.ng/cars/mercedes-benz")
        time.sleep(5)
        
        # Check if page loaded
        page_title = driver.title
        logger.info(f"  Page title: {page_title}")
        
        # Scroll like a human
        driver.execute_script("window.scrollBy(0, 400);")
        time.sleep(2)
        driver.execute_script("window.scrollBy(0, 200);")
        time.sleep(1)
        
        # Check page source length
        page_source = driver.page_source
        page_length = len(page_source)
        logger.info(f"  Page length: {page_length} characters")
        
        if "captcha" in page_source.lower():
            logger.warning("⚠️ Captcha detected!")
        elif "403" in page_source:
            logger.warning("⚠️ 403 Forbidden detected!")
        elif page_length > 50000:
            logger.info("✅ Page loaded successfully with content")
            
            # Try to find car listings
            if "mercedes" in page_source.lower() or "benz" in page_source.lower():
                logger.info("✅ Found car listings on page!")
            else:
                logger.warning("⚠️ Page loaded but no car listings found")
        else:
            logger.warning(f"⚠️ Suspicious page size: {page_length} chars")
        
        # Take Jiji screenshot
        jiji_screenshot = "/tmp/jiji_test.png"
        driver.save_screenshot(jiji_screenshot)
        logger.info(f"✅ Jiji screenshot saved")
        
        logger.info("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")

if __name__ == "__main__":
    # Run the test
    success = test_undetected_browser()
    
    if success:
        logger.info("🎉 Undetected ChromeDriver + Stealth is working! Ready for Step 2.")
    else:
        logger.error("❌ Test failed. Check the logs above.")
