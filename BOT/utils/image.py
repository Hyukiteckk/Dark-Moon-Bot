import re
import aiohttp

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def is_valid_image_url(url: str) -> bool:
    if not url:
        return False

    url = url.lower()

    if not url.startswith(("http://", "https://")):
        return False

    return url.endswith(IMAGE_EXTENSIONS)

