#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Download curated high-resolution Islamic images for hadith cards.
Run this once to populate the .image_cache directory.
"""

import os
import requests
from pathlib import Path

# Curated free Islamic images from Unsplash (no API key needed for specific photo URLs)
CURATED_ISLAMIC_IMAGES = [
    # Mosques & Islamic Architecture
    "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1080",  # Mosque interior
    "https://images.unsplash.com/photo-1564769610726-4bae494b1eb4?w=1080",  # Mecca aerial
    "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1080",  # Mosque dome
    "https://images.unsplash.com/photo-1580418827493-f2b22c0a76cb?w=1080",  # Kaaba
    "https://images.unsplash.com/photo-1542816417-0983c9c9ad53?w=1080",  # Blue mosque
    
    # Quran & Prayer
    "https://images.unsplash.com/photo-1609599006353-e629aaabfeae?w=1080",  # Quran open
    "https://images.unsplash.com/photo-1610729483869-c051e86ca22d?w=1080",  # Prayer beads
    "https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=1080",  # Quran and dates
    "https://images.unsplash.com/photo-1590650153855-d9e808231d41?w=1080",  # Prayer mat
    
    # Islamic Calligraphy & Art
    "https://images.unsplash.com/photo-1591604129939-f1efa4d9f7fa?w=1080",  # Arabic calligraphy
    "https://images.unsplash.com/photo-1609599006353-e629aaabfeae?w=1080",  # Islamic patterns
    "https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=1080",  # Geometric patterns
]

CACHE_DIR = Path(__file__).parent / ".image_cache"

def download_images():
    """Download all curated Islamic images to cache directory."""
    CACHE_DIR.mkdir(exist_ok=True)
    
    print(f"📥 Downloading {len(CURATED_ISLAMIC_IMAGES)} Islamic images...")
    
    for idx, url in enumerate(CURATED_ISLAMIC_IMAGES, 1):
        filename = f"islamic_{idx:02d}.jpg"
        filepath = CACHE_DIR / filename
        
        if filepath.exists():
            print(f"  ✓ {filename} already exists")
            continue
        
        try:
            print(f"  📥 Downloading {filename}...", end=" ")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✓ ({len(response.content) // 1024} KB)")
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    print(f"\n✅ Completed! Images saved to: {CACHE_DIR}")
    print(f"   Total files: {len(list(CACHE_DIR.glob('*.jpg')))}")

if __name__ == "__main__":
    download_images()
