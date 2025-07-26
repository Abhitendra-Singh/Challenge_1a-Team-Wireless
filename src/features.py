import re

def extract_features(line_data):
    """
    Extracts advanced features from a line's data, including relative font size and position.
    """
    text = line_data['text']
    font_size = line_data.get('size', 0)
    avg_font_size = line_data.get('avg_size', 1) # Avoid division by zero
    
    features = {
        'length': len(text),
        'word_count': len(text.split()),
        'is_all_caps': 1 if text.isupper() and len(text) > 1 else 0,
        'starts_with_number': 1 if re.match(r'^\d+(\.\d+)*', text) else 0,
        
        # --- Advanced Features ---
        'font_size': font_size,
        'is_bold': 1 if 'bold' in line_data.get('font', '').lower() else 0,
        
        # Is the font size significantly larger than the page average?
        'relative_size': font_size / avg_font_size if avg_font_size > 0 else 0,
        
        # Is the line in the top 15% of the page? (Titles/headers often are)
        'is_top_of_page': 1 if line_data.get('y0', 1000) < line_data.get('page_height', 800) * 0.15 else 0,
    }
    return features
