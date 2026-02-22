#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests

# --- CONFIGURATION ---
API_KEY = "IsIJkYtZHvShldKP3sCfQQymyFMaemc0ZcmDvr1mGA4nfCs5FtskQv1e"
SEARCH_QUERY = "Islamic art 4k"
IMAGES_NEEDED = 100
RESULTS_PER_PAGE = 50

# Absolute path to your existing cache folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FOLDER = os.path.join(BASE_DIR, ".image_cache")
# ---------------------

def download_images():
    # Ensure the cache folder exists
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    
    # Authenticate with Pexels
    headers = {"Authorization": API_KEY}
    
    images_downloaded = 0
    page = 1
    
    print(f"Starting bulk download of {IMAGES_NEEDED} images...")
    
    while images_downloaded < IMAGES_NEEDED:
        # Request a page of results from the API
        url = f"https://api.pexels.com/v1/search?query={SEARCH_QUERY}&per_page={RESULTS_PER_PAGE}&page={page}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print("Error: Could not fetch from Pexels. Check your API key.")
            break
            
        data = response.json()
        photos = data.get("photos", [])
        
        if not photos:
            print("Notice: No more unique images found for this search query.")
            break
            
        for photo in photos:
            if images_downloaded >= IMAGES_NEEDED:
                break
                
            # 'large2x' provides high-resolution, uncompressed quality
            img_url = photo["src"]["large2x"] 
            img_id = photo["id"]
            
            try:
                # Download the actual image file
                img_data = requests.get(img_url, timeout=15).content
                file_path = os.path.join(SAVE_FOLDER, f"bg_{img_id}.jpg")
                
                # Save it to the .image_cache folder
                with open(file_path, "wb") as f:
                    f.write(img_data)
                    
                images_downloaded += 1
                print(f"[{images_downloaded}/{IMAGES_NEEDED}] Successfully saved image ID: {img_id}")
            except Exception as e:
                print(f"Failed to download image {img_id}: {e}")
                
        # Move to the next page of search results
        page += 1
        
    print("\n✅ Bulk download complete! Your .image_cache folder is ready.")

if __name__ == "__main__":
    download_images()