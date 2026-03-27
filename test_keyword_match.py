from external_services.gov_services_map import SERVICE_KEYWORDS

def _calculate_keyword_match(transcript: str, keywords_dict: dict) -> float:
    if not keywords_dict:
        return 0.0
    
    transcript_lower = transcript.lower()
    matches = 0
    total_keywords = 0
    
    # Flatten the dict of lists into a single list of strings
    all_keywords = []
    for key, value in keywords_dict.items():
        if isinstance(value, list) and key in ["hindi", "english", "marathi"]:
            all_keywords.extend(value)
            
    if not all_keywords:
        return 0.0
        
    for kw in all_keywords:
        if kw.lower() in transcript_lower:
            matches += 1
            
    # Give a good score if at least one or two keywords match
    if matches >= 2:
        return 1.0
    elif matches == 1:
        return 0.8
    return 0.0

print(_calculate_keyword_match("पानी नहीं आ रहा", SERVICE_KEYWORDS["water"]))
