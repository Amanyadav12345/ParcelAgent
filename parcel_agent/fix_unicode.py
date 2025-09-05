#!/usr/bin/env python3
import re

# Read the api_service.py file
with open('src/services/api_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all Unicode emojis with simple text alternatives
replacements = {
    '🏙️': '',
    '📊': '',
    '✓': '',
    '✅': '',
    '❌': '',
    '🎨': '',
    '🔍': '',
    '🔗': '',
    '📋': '',
    '⚠️': '',
    '⭐': ''
}

for emoji, replacement in replacements.items():
    content = content.replace(emoji, replacement)

# Write back the cleaned content
with open('src/services/api_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Unicode characters removed from api_service.py")