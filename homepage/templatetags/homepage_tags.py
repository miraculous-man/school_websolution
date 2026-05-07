import re
from django import template

register = template.Library()


def _extract_youtube_id(url):
    if not url:
        return None
    url = str(url).strip()
    patterns = [
        r'youtu\.be/([A-Za-z0-9_\-]{11})',
        r'youtube\.com/shorts/([A-Za-z0-9_\-]{11})',
        r'youtube\.com/embed/([A-Za-z0-9_\-]{11})',
        r'youtube\.com/watch\?v=([A-Za-z0-9_\-]{11})',
        r'youtube\.com/v/([A-Za-z0-9_\-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


@register.filter
def replace(value, arg):
    if ',' not in arg:
        return value
    old, new = arg.split(',', 1)
    return str(value).replace(old, new)


@register.filter
def youtube_embed(url):
    vid_id = _extract_youtube_id(url)
    if vid_id:
        return f'https://www.youtube.com/embed/{vid_id}'
    return str(url)


@register.filter
def youtube_id(url):
    return _extract_youtube_id(url) or ''


@register.filter
def youtube_thumbnail(url):
    vid_id = _extract_youtube_id(url)
    if vid_id:
        return f'https://img.youtube.com/vi/{vid_id}/hqdefault.jpg'
    return ''


@register.filter
def is_youtube(url):
    if not url:
        return False
    return 'youtube.com' in str(url) or 'youtu.be' in str(url)
