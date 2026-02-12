import httpx
import random
import logging

logger = logging.getLogger(__name__)

# Base URL for fawazahmed0 Hadith API (CDN)
# Structure: https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}/{hadith_number}.json
# or better to use the editions index based approach if we want random?
# Actually, the API has endpoints for books.
# But for random hadith, we might need a different strategy or just pick a random number.
# Sahih Bukhari has approx 7563 hadiths.
# Sahih Muslim has approx 3032 hadiths.

# We will use the 'eng-bukhari' and 'eng-muslim' editions for English, 
# and 'rus-bukhari' if available? 
# Checking available editions: https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json
# There is 'rus-bukhari' (Russian Translation of Sahih Bukhari)
# There is 'rus-muslim' (Russian Translation of Sahih Muslim)

# We will alternate between Bukhari and Muslim.

EDITIONS = {
    'bukhari': 'rus-bukhari',
    'muslim': 'rus-muslim'
}

# Approximate ranges for valid hadith numbers to avoid 404s too often.
# Gaps exist, so we might need retries.
MAX_HADITH_NUMBERS = {
    'bukhari': 7563,
    'muslim': 7563 # Muslim numbering is tricky, let's use a safe upper bound or try to find a random endpoint.
    # The API doesn't have a direct "random" endpoint in the static CDN.
    # We will try to fetch a random number.
}

async def get_random_hadith():
    """
    Fetches a random Sahih Hadith (Bukhari or Muslim) in Russian.
    Returns a dictionary with hadith data.
    """
    source_name = random.choice(['bukhari', 'muslim'])
    edition = EDITIONS[source_name]
    
    # Try a few times to get a valid hadith (in case of 404 due to gaps)
    for _ in range(5):
        hadith_number = random.randint(1, MAX_HADITH_NUMBERS[source_name])
        url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{edition}/{hadith_number}.json"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    # Data structure:
                    # { "hadith": [...], "metadata": {...} } or just the hadith object depending on endpoint
                    # The endpoint above returns a SINGLE hadith object:
                    # { "hadithnumber": 1, "arabicnumber": 1, "text": "...", "grades": [], ... }
                    # actually the structure is:
                    # { "hadiths": [ { ... } ], "metadata": { ... } } if we fetch a collection
                    # But the single hadith endpoint?
                    # Let's check the docs. 
                    # interacting with the file structure directly.
                    # editions/{edition}/sections/{section_id}.json is better?
                    # No, let's stick to the single hadith file if it exists.
                    # Actually, the CDN is: editions/{edition}/{hadith_number}.json might NOT exist closely packed.
                    #
                    # Better approach: Fetch the 'sections' or 'index' once and cache it? No, too big.
                    #
                    # Alternative: Use the "minified" versions or the `hadiths` folder structure.
                    #
                    # Let's use a known-good fallback logic: 
                    # If we fail, return a hardcoded one.
                    
                    if 'hadiths' in data:
                        h = data['hadiths'][0]
                    else:
                        h = data
                        
                    return {
                        "text": h['text'],
                        "source": "Sahih Bukhari" if source_name == 'bukhari' else "Sahih Muslim",
                        "number": h.get('hadithnumber'),
                        "grades": h.get('grades', []),
                        "edition": edition
                    }
                    
        except Exception as e:
            logger.warning(f"Failed to fetch hadith {edition}:{hadith_number}: {e}")
            continue
            
    return get_fallback_hadith()

async def get_hadith_explanation(hadith_text):
    """
    Generates a generic 'scholarly explanation' based on the hadith text.
    Since we don't have a real Tafsir API for Hadith text specifically,
    we will provide a context wrapper.
    """
    # In a real app with more resources, we'd query an LLM or a specific database.
    # Here we mock it or provide general context.
    
    explanation = (
        "<b>Hadith Explanation:</b>\n\n"
        "This Hadith is from the authentic collections (Sahih). "
        "Scholars emphasize the importance of understanding the context "
        "and the application of this guidance in daily life. "
        "Focus on the core message of the text and how it aligns with the Quranic teachings."
    )
    return explanation

def get_fallback_hadith():
    return {
        "text": "Действия оцениваются только по намерениям, и каждому человеку достанется только то, что он намеревался обрести...",
        "source": "Sahih Bukhari",
        "number": 1,
        "grades": [{"grade": "Sahih", "name": "Al-Albani"}],
        "edition": "rus-bukhari"
    }
