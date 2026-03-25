#!/usr/bin/env python3
"""
INTERACTIVE URGENCY TESTER
==========================
Type complaints and instantly see how the system rates them.
Perfect for testing the urgency detection system without microphone.
"""

import sys
from collections import defaultdict

class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


URGENCY_KEYWORDS = {
    "CRITICAL": {
        "hindi": ["आग", "आग लगी", "fire", "emergency", "तुरंत", "जल्दी", "तुरंत ही", "बहुत खतरनाक", 
                  "मेरी जान", "जान का खतरा", "घायल", "खून", "गंभीर", "accident", "दुर्घटना",
                  "collision", "टकराव", "ज्यादा चोट", "serious"],
        "english": ["fire", "emergency", "urgent", "critical", "critical level", "danger", "help", "911", "dying", 
                    "severe", "accident", "bleeding", "unconscious", "dead", "police", "attack", "shot"]
    },
    "HIGH": {
        "hindi": ["बिजली", "बिजली नहीं", "बिजली गई", "बिजली खत्म", "कोई आ रहा है", "चोर", "डाका", "गायब", "खो गया", 
                  "अस्पताल", "बीमार", "बहुत बीमार", "दर्द", "बहुत दर्द", "तकलीफ", "पानी समस्या", "पानी नहीं"],
        "english": ["electricity", "power", "no power", "cut off", "theft", "robbery", "missing", "lost", 
                    "hospital", "sick", "illness", "pain", "suffer", "medical", "urgent care"]
    },
    "MEDIUM": {
        "hindi": ["तोड़ा", "तोड़", "खराब", "नहीं काम", "काम नहीं", "समस्या", "issue", "गड्ढा", "गड्ढे", "पानी", 
                  "सड़क", "गली", "स्कूल", "पार्क", "बस", "ट्रेन", "कूड़ा", "कचरा", "साफ सफाई"],
        "english": ["broken", "damage", "damaged", "not working", "not working", "problem", "issue", "pothole", 
                    "water", "drain", "road", "street", "school", "park", "bus", "train", "garbage", "trash"]
    },
    "LOW": {
        "hindi": ["सुझाव", "शिकायत", "पूछना", "जानकारी", "आवेदन", "स्थिति", "कब", "कहाँ", "क्या"],
        "english": ["suggestion", "complaint", "question", "information", "application", "status", "when", "where", "what"]
    }
}


def analyze_urgency(text):
    """Analyze text for urgency."""
    text_lower = text.lower()
    found_keywords = []
    max_urgency = "LOW"
    scores = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    max_score = 0
    
    for urgency, keywords_dict in URGENCY_KEYWORDS.items():
        all_keywords = keywords_dict.get("hindi", []) + keywords_dict.get("english", [])
        for keyword in all_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
                score = scores.get(urgency, 0)
                if score > max_score:
                    max_score = score
                    max_urgency = urgency
    
    return max_urgency, found_keywords, max_score


def get_color_icon(urgency):
    """Get color and icon for urgency."""
    icons = {
        "CRITICAL": ("🚨", Colors.RED),
        "HIGH": ("⚠️", Colors.YELLOW),
        "MEDIUM": ("⏱️", Colors.BLUE),
        "LOW": ("ℹ️", Colors.GREEN),
    }
    return icons.get(urgency, ("•", Colors.END))


def display_result(text, urgency, keywords, score):
    """Display analysis result."""
    icon, color = get_color_icon(urgency)
    
    print(f"\n  Input: {Colors.CYAN}\"{text}\"{Colors.END}")
    print(f"  {color}{icon} Urgency: {urgency}{Colors.END} (Score: {score}/4)")
    
    if keywords:
        unique_kw = list(set(keywords))[:5]
        print(f"  Keywords: {Colors.YELLOW}{', '.join(unique_kw)}{Colors.END}")
    else:
        print(f"  {Colors.DIM}(No keywords detected){Colors.END}")


def print_header():
    """Print header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}  INTERACTIVE URGENCY TESTER{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.DIM}  Type complaints and see instant urgency classification{Colors.END}")
    print(f"{Colors.DIM}  Supports: Hindi, English, Hinglish (Mixed){Colors.END}")
    print(f"{Colors.DIM}  Type 'exit' or 'quit' to leave{Colors.END}\n")


def print_examples():
    """Print usage examples."""
    print(f"{Colors.BOLD}Examples (try these):{Colors.END}")
    print(f"  {Colors.RED}🚨 CRITICAL:{Colors.END} 'आग लगी मेरे घर में'")
    print(f"  {Colors.YELLOW}⚠️  HIGH:{Colors.END} 'बिजली गई 5 दिन से'")
    print(f"  {Colors.BLUE}⏱️  MEDIUM:{Colors.END} 'सड़क में बड़ा गड्ढा है'")
    print(f"  {Colors.GREEN}ℹ️  LOW:{Colors.END} 'स्कूल की जानकारी चाहिए'\n")


def main():
    """Main loop."""
    print_header()
    print_examples()
    
    stats = defaultdict(int)
    
    while True:
        try:
            user_input = input(f"{Colors.BOLD}>>{Colors.END} ").strip()
            
            if not user_input:
                print(f"  {Colors.DIM}(empty input, try again){Colors.END}")
                continue
            
            if user_input.lower() in ["exit", "quit", "e", "q"]:
                break
            
            urgency, keywords, score = analyze_urgency(user_input)
            stats[urgency] += 1
            
            display_result(user_input, urgency, keywords, score)
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  {Colors.RED}Error: {e}{Colors.END}")
    
    # Summary
    if stats:
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}")
        print(f"{Colors.CYAN}  Session Summary{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'─'*80}{Colors.END}")
        total = sum(stats.values())
        print(f"  Complaints processed: {total}")
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = stats.get(level, 0)
            pct = (count / total * 100) if total > 0 else 0
            icon, color = get_color_icon(level)
            print(f"  {color}{icon} {level:10}: {count:3} ({pct:5.1f}%){Colors.END}")
    
    print(f"\n{Colors.GREEN}✓ Goodbye!{Colors.END}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted{Colors.END}\n")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}\n")
