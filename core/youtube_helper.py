import re

def get_youtube_embed_url(youtube_url):
    # Extract video ID from common YouTube URL formats
    # This regex handles watch?v=, v/, embed/, youtu.be/, and mobile formats
    regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/|youtube-nocookie\.com\/embed\/)([a-zA-Z0-9_-]{11})'
    
    # Clean the URL
    clean_url = str(youtube_url or '').strip()
    match = re.search(regex, clean_url)
    
    if match:
        video_id = match.group(1)
        # Use standard YouTube embed URL.
        return f"https://www.youtube.com/embed/{video_id}"
    
    # Fallback for manual embed codes
    if 'embed/' in clean_url:
        if clean_url.startswith('//'):
            return f"https:{clean_url}"
        return clean_url
        
    return clean_url
