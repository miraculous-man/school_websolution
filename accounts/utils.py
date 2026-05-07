from PIL import Image
from collections import Counter


def extract_dominant_colors(image_path, num_colors=5):
    """Extract dominant colors from an image and return as hex codes."""
    try:
        img = Image.open(image_path)
        img = img.resize((150, 150))
        img = img.convert('RGB')
        
        pixels = list(img.getdata())
        
        pixel_counts = Counter(pixels)
        most_common = pixel_counts.most_common(num_colors)
        
        colors = []
        for rgb, _ in most_common:
            hex_color = '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
            colors.append(hex_color)
        
        return colors if colors else ['#0d6efd', '#6c757d', '#198754', '#2c3e50', '#34495e']
    except Exception as e:
        print(f"Error extracting colors: {e}")
        return ['#0d6efd', '#6c757d', '#198754', '#2c3e50', '#34495e']


def get_contrasting_color(hex_color):
    """Get a contrasting color (light or dark) based on background color."""
    try:
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return '#ffffff' if luminance < 0.5 else '#333333'
    except:
        return '#333333'
