# config.py
import os

# 🔐 TELEGRAM SETTINGS
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Target Locations in Abuja
ABUJA_AREAS = [
    'abuja', 'fct', 'garki', 'wuse', 'maitama', 'asokoro', 
    'gwarinpa', 'kubwa', 'nyanya', 'karu', 'jabi', 'utako',
    'wuye', 'life camp', 'apo', 'lugbe', 'kado', 'gudu',
    'guzape', 'durumi', 'katampe', 'dawaki', 'gwagwalada'
]

# Target Cars (Benz, Lexus, Toyota)
TARGET_MAKES = {
    'mercedes': ['mercedes', 'benz', 'c300', 'e350', 'gle', 'glk', 'c200', 'e200', 's-class', 'ml', 'c250', 'e250', 'gl450', 'glk350', 'amg'],
    'lexus': ['lexus', 'rx350', 'rx330', 'rx300', 'es350', 'gx460', 'lx570', 'gs', 'ls', 'rx400', 'rx450', 'es300', 'gx470'],
    'toyota': ['venza', 'avalon', 'camry', 'toyota venza', 'toyota avalon', 'toyota camry', 'camry le', 'camry se', 'avalon limited']
}

# Distress Keywords (with weights)
DISTRESS_KEYWORDS = {
    # Primary (+5 each)
    'distress sale': 5, 'urgent sale': 5, 'must sell': 5, 'need cash': 5,
    'desperate': 5, 'emergency': 5, 'quick sale': 5, 'urgent': 3,
    
    # Life Events (+4 each)
    'relocation': 4, 'relocating': 4, 'leaving abroad': 4, 'travelling': 4,
    'moving abroad': 4, 'change of plan': 4, 'travelling soon': 4,
    
    # Price Related (+3 each)
    'price crash': 3, 'below market': 3, 'cheap offer': 3, 'negotiable': 3,
    'best offer': 3, 'price reduced': 3, 'slashed price': 3, 'price slash': 3,
    'give away': 3, 'almost free': 3,
    
    # Time Pressure (+3 each)
    'today only': 3, 'this week': 3, 'month end': 3, 'last price': 3,
    'before weekend': 3, 'first come': 3,
    
    # Secondary (+1 each)
    'discount': 1, 'sale': 1, 'clearance': 1, 'asap': 1, 'now': 1,
    'price drop': 1, 'dropped': 1
}

# Nigerian Pidgin Distress Keywords
PIDGIN_KEYWORDS = {
    'urgent': 3, 'quick quick': 4, 'cash urgent': 5, 'price drop': 2,
    'serious buyer': 2, 'gift': 1, 'running': 2, 'abeg': 1
}

# Combine all keywords
ALL_DISTRESS_KEYWORDS = list(DISTRESS_KEYWORDS.keys()) + list(PIDGIN_KEYWORDS.keys())

# Scan settings
SCAN_INTERVAL_MINUTES = 10
REQUEST_TIMEOUT = 15
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1'
]
