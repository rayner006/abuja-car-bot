# ============================================
# CONFIGURATION - WITH TELEGRAM INTEGRATION
# ============================================

import os

# 🔐 TELEGRAM SETTINGS (Get from Render Environment Variables)
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
    'BENZ': ['mercedes', 'benz', 'c300', 'e350', 'gle', 'glk', 'c200', 'e200', 's-class', 'ml', 'c250', 'e250', 'gl450'],
    'LEXUS': ['lexus', 'rx350', 'rx330', 'rx300', 'es350', 'gx460', 'lx570', 'gs', 'ls', 'rx400', 'rx450'],
    'TOYOTA': ['venza', 'avalon', 'camry', 'toyota venza', 'toyota avalon', 'toyota camry']
}

# Distress Keywords (with weights)
DISTRESS_KEYWORDS = {
    # Primary (+5 each)
    'distress sale': 5, 'urgent sale': 5, 'must sell': 5, 'need cash': 5,
    'desperate': 5, 'emergency': 5, 'quick sale': 5,
    
    # Life Events (+4 each)
    'relocation': 4, 'relocating': 4, 'leaving abroad': 4, 'travelling': 4,
    'moving abroad': 4, 'change of plan': 4,
    
    # Price Related (+3 each)
    'price crash': 3, 'below market': 3, 'cheap offer': 3, 'negotiable': 3,
    'best offer': 3, 'price reduced': 3, 'slashed price': 3,
    
    # Time Pressure (+3 each)
    'today only': 3, 'this week': 3, 'month end': 3, 'last price': 3,
    
    # Secondary (+1 each)
    'discount': 1, 'sale': 1, 'clearance': 1, 'asap': 1, 'now': 1
}

# Scan settings
SCAN_INTERVAL_MINUTES = 10
