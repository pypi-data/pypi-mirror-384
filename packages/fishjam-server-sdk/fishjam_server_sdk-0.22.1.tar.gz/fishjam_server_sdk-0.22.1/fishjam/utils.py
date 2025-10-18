from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False


def get_fishjam_url(fishjam_id: str) -> str:
    if not validate_url(fishjam_id):
        return f"https://fishjam.io/api/v1/connect/{fishjam_id}"

    return fishjam_id
