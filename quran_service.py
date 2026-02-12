import httpx
import random
import logging

logger = logging.getLogger(__name__)

# Base URL for Al-Quran Cloud API
API_BASE_URL = "http://api.alquran.cloud/v1"

# Editions
EDITION_ARABIC = "quran-uthmani"
EDITION_RUSSIAN = "ru.kuliev"
EDITION_TAFSIR_QURTUBI = "ar.qurtubi"
EDITION_TAFSIR_ENGLISH = "en.qaribullah" # Closest to Qushayri style currently available

async def get_random_ayah():
    """
    Fetches a random ayah with Arabic text and Russian translation.
    Returns a dictionary with ayah data or None if failed.
    """
    # approx 6236 ayahs in Quran. 
    # The API actually supports /ayah/random, but we want specific editions.
    # We can use http://api.alquran.cloud/v1/ayah/random/editions/quran-uthmani,ru.kuliev
    
    url = f"{API_BASE_URL}/ayah/random/editions/{EDITION_ARABIC},{EDITION_RUSSIAN}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200 and data.get("data"):
                # data['data'] is a list of 2 items (one for each edition)
                # Structure:
                # [
                #   { "text": "...", "surah": {...}, "number": ..., "numberInSurah": ... }, # Arabic
                #   { "text": "...", ... } # Russian
                # ]
                
                arabic_data = data['data'][0]
                russian_data = data['data'][1]
                
                return {
                    "surah_number": arabic_data['surah']['number'],
                    "surah_name": arabic_data['surah']['name'],
                    "surah_english_name": arabic_data['surah']['englishName'],
                    "ayah_number": arabic_data['numberInSurah'],
                    "text_arabic": arabic_data['text'],
                    "text_russian": russian_data['text'],
                    "audio": arabic_data.get('audio'), # basic edition might not have audio, but just in case
                    "global_ayah_number": arabic_data['number']
                }
            else:
                logger.error(f"API Error: {data}")
                return get_fallback_ayah()
                
    except Exception as e:
        logger.error(f"Network Error in get_random_ayah: {e}")
        return get_fallback_ayah()

async def get_ayah(surah, ayah):
    """
    Fetches a specific ayah by surah and number.
    """
    # Ref format: surah:ayah
    ref = f"{surah}:{ayah}"
    url = f"{API_BASE_URL}/ayah/{ref}/editions/{EDITION_ARABIC},{EDITION_RUSSIAN}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200 and data.get("data"):
                arabic_data = data['data'][0]
                russian_data = data['data'][1]
                
                return {
                    "surah_number": arabic_data['surah']['number'],
                    "surah_name": arabic_data['surah']['name'],
                    "surah_english_name": arabic_data['surah']['englishName'],
                    "ayah_number": arabic_data['numberInSurah'],
                    "text_arabic": arabic_data['text'],
                    "text_russian": russian_data['text'],
                    "global_ayah_number": arabic_data['number']
                }
    except Exception as e:
        logger.error(f"Error getting ayah {surah}:{ayah}: {e}")
    return None

async def get_tafsir_qurtubi(surah, ayah):
    """
    Fetches Tafsir Al-Qurtubi (Arabic).
    """
    return await _get_tafsir(surah, ayah, EDITION_TAFSIR_QURTUBI, "Al-Qurtubi")

async def get_tafsir_qushayri(surah, ayah):
    """
    Fetches English Tafsir (using Qaribullah as proxy for Qushayri-style spiritual commentary).
    """
    return await _get_tafsir(surah, ayah, EDITION_TAFSIR_ENGLISH, "English Tafsir")

async def _get_tafsir(surah, ayah, edition, name):
    ref = f"{surah}:{ayah}"
    url = f"{API_BASE_URL}/ayah/{ref}/{edition}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200 and data.get("data"):
                 return {
                    "text": data['data']['text'],
                    "edition_name": data['data']['edition']['name'],
                    "scholar_name": name
                 }
    except Exception as e:
        logger.error(f"Error fetching tafsir {edition} for {surah}:{ayah}: {e}")
        return None
        
def get_fallback_ayah():
    """
    Returns a hardcoded sample ayah in case of API failure.
    Surah Al-Fatiha 1:1
    """
    return {
        "surah_number": 1,
        "surah_name": "سورة الفاتحة",
        "surah_english_name": "Al-Fatiha",
        "ayah_number": 1,
        "text_arabic": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
        "text_russian": "Во имя Аллаха, Милостивого, Милосердного!",
        "global_ayah_number": 1
    }
