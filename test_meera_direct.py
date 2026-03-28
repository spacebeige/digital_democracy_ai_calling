#!/usr/bin/env python3
"""
Direct test of Meera 10-step pipeline without requiring microphone input.
Tests Meera with various complaint texts in different languages.
"""

import asyncio
import json
from datetime import datetime
import sys
import os

# Add path
sys.path.insert(0, '/home/parth/Desktop/delhi')
os.environ['CUDA_VISIBLE_DEVICES'] = ''

# Import after CUDA disable
from interactive_voice_to_layer3_integrated import MeeraAssistant, Colors, create_session_id

# Sample complaints in different languages
TEST_COMPLAINTS = {
    "Hindi - Angry": {
        "text": "मेरा ऑर्डर 5 दिन से नहीं आया!! बहुत गुस्से में हूँ!! तुरंत डिलीवरी करो या रिफंड दो!",
        "lang": "Hindi"
    },
    "English - Urgent": {
        "text": "IMMEDIATELY I need this resolved! I've been waiting for 2 weeks with no response. This is unacceptable!",
        "lang": "English"
    },
    "Marathi - Query": {
        "text": "नमस्कार, मला माझ्या ऑर्डर क्रमांक OR2024-5678 चे स्टेटस जाणून घायचे आहे. कृपया सहाय्य करा.",
        "lang": "Marathi"
    },
    "Tamil - Problem": {
        "text": "எனது பரிமாண விவரங்கள் தவறாக உள்ளன. தயவுசெய்து உடனடியாக சரிசெய்யவும்.",
        "lang": "Tamil"
    },
    "Urdu - High Urgency": {
        "text": "براہ کرم فوری طور پر مدد کریں! آپ کی طرف سے کوئی جواب نہیں ملا۔ ہزار روپے کی ادائیگی روک دی گئی ہے۔",
        "lang": "Urdu"
    }
}


async def test_meera():
    """Test Meera with sample complaints"""
    
    print(f"\n{'='*80}")
    print("🧠 MEERA ASSISTANT - DIRECT PIPELINE TEST (NO MICROPHONE REQUIRED)")
    print(f"{'='*80}\n")
    
    meera = MeeraAssistant()
    session_id = create_session_id()
    
    results = []
    
    for test_name, test_data in TEST_COMPLAINTS.items():
        print(f"\n{Colors.CYAN}█ TEST: {test_name}{Colors.END}")
        print(f"  Input: {test_data['text'][:70]}...")
        print(f"  {Colors.YELLOW}Processing through 10-step pipeline...{Colors.END}")
        
        # Process through Meera's 10-step pipeline
        meera_result = await meera.process_input(test_data['text'], session_id)
        
        # Display results
        print(f"\n  {Colors.CYAN}[MEERA PROCESSING RESULT]{Colors.END}")
        print(f"    ✓ Language: {meera_result['lang_name']} ({meera_result['lang_code']})")
        print(f"    ✓ Intent: {meera_result['intent']}")
        print(f"    ✓ Emotion: {meera_result['emotion']} (anger: {meera_result['anger_score']:.2f})")
        print(f"    ✓ Urgency: {meera_result['urgency']}")
        
        if meera_result['entities']:
            entities_str = ", ".join([f"{k}={v}" for k, v in list(meera_result['entities'].items())[:3]])
            print(f"    ✓ Entities: {entities_str}")
        
        print(f"\n  {Colors.YELLOW}[MEERA RESPONSE]{Colors.END}")
        print(f"    \"{meera_result['response']}\"")
        
        results.append({
            'test_name': test_name,
            'input': test_data['text'],
            'meera_result': meera_result,
            'timestamp': datetime.now().isoformat()
        })
    
    # Save detailed results to JSON
    output_dir = "outputs/json_results/meera_test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f"{output_dir}/meera_direct_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"✅ TEST COMPLETE - All 10-step pipelines executed successfully")
    print(f"📁 Results saved: {output_file}")
    print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")
    
    # Print summary table
    print(f"\n{Colors.YELLOW}SUMMARY TABLE{Colors.END}")
    print(f"{'Test':<25} {'Language':<12} {'Intent':<12} {'Emotion':<10} {'Urgency':<10}")
    print("-" * 69)
    
    for result in results:
        mr = result['meera_result']
        print(f"{result['test_name']:<25} {mr['lang_name']:<12} {mr['intent']:<12} {mr['emotion']:<10} {mr['urgency']:<10}")
    
    print()


if __name__ == "__main__":
    try:
        asyncio.run(test_meera())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⏹️  Test interrupted{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.CYAN}❌ Error: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
