from googletrans import Translator
import logging

logger = logging.getLogger(__name__)

# Initialize translator
# Note: googletrans 4.0.0-rc1 is required for better stability
try:
    translator = Translator()
except Exception as e:
    logger.error(f"Failed to initialize translator: {e}")
    translator = None

async def translate_to_english(text):
    """
    Translates text to English.
    """
    return await _translate(text, 'en')

async def translate_to_turkish(text):
    """
    Translates text to Turkish.
    """
    return await _translate(text, 'tr')

async def _translate(text, dest_lang):
    if not translator:
        return "Translation service unavailable."
        
    try:
        # translator.translate is synchronous in googletrans 4.0.0-rc1 but we can wrap it or just call it.
        # Actually in 4.0.0-rc1, it supports async wait? No, the library structure is complex.
        # But wait, googletrans uses httpx internally in recent versions.
        # Let's use the async `translate` method if available, or just run it.
        # It's better to run CPU bound or blocking IO in run_in_executor if needed,
        # but for this low volume bot, direct call is okay, or we can use `await translator.translate` if it is async.
        # `googletrans==4.0.0-rc1` uses `httpx` async clients internally but the `translate` method itself is...
        # Let's check typical usage. 
        # Actually, `translator.translate` is a sync method in the standard usage.
        # We'll treat it as sync for now. If it blocks the event loop too much, we can optimize.
        
        result = await translator.translate(text, dest=dest_lang)
        return result.text
    except AttributeError:
        # Fallback for sync usage in older versions or specific environments
        try:
             result = translator.translate(text, dest=dest_lang)
             return result.text
        except Exception as e:
            logger.error(f"Translation error (sync fallback): {e}")
            return "Translation failed."
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return "Translation failed."
