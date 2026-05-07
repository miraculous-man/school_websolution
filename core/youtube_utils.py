import re

def get_youtube_embed_url(youtube_url):
    """
    Standardizes YouTube URLs to a reliable embed format.
    Handles watch?v=, v/, embed/, youtu.be/, and mobile formats.
    """
    if not youtube_url:
        return ""
        
    # Standard YouTube ID regex
    regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube-nocookie\.com\/embed\/)([a-zA-Z0-9_-]{11})'
    
    clean_url = str(youtube_url).strip()
    match = re.search(regex, clean_url)
    
    if match:
        video_id = match.group(1)
        # Standard embed is often more reliable than nocookie for restricted accounts
        return f"https://www.youtube.com/embed/{video_id}"
    
    # Pass through if already looks like an embed URL
    if 'embed/' in clean_url:
        if clean_url.startswith('//'):
            return f"https:{clean_url}"
        return clean_url
        
    return clean_url
