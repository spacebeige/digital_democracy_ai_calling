import re
import sys

def main():
    try:
        with open('interactive_voice_to_layer3_integrated.py', 'r') as f:
            text = f.read()

        # 1. Update imports
        text = text.replace(
            "from scheme_classifier import classify_scheme, classify_scheme_async",
            "from scheme_classifier import classify_scheme, classify_scheme_async\nfrom db_scheme_fetcher import fetch_schemes_from_neon"
        )

        # 2. Update generate_groq_response signature
        old_sig = """async def generate_groq_response(transcript: str, language: str, urgency: str, intent: str, service_name: str, 
                                  vulgarity_result: Dict = None, ticket_number: str = None,
                                  is_scheme_enquiry: bool = False, state_code: str = None) -> str:"""
        new_sig = """async def generate_groq_response(transcript: str, language: str, urgency: str, intent: str, service_name: str, 
                                  vulgarity_result: Dict = None, ticket_number: str = None,
                                  is_scheme_enquiry: bool = False, state_code: str = None,
                                  department: str = "general", db_scheme_data: dict = None) -> str:"""
        
        if old_sig in text:
            text = text.replace(old_sig, new_sig)
        else:
            print("Warning: old_sig not found!")

        # 3. Update ticket_context to include helplines
        old_context = """        # Build context about ticket or scheme
        ticket_context = ""
        if ticket_number:
            ticket_context = f"\\nTicket Number: {ticket_number} (Please tell user this ticket number)"
        elif is_scheme_enquiry:"""
                
        new_context = """        # Pro Helpline Mapping
        HELPLINES = {
            "fire": "101 or 112 (National Emergency)",
            "police": "100 or 112",
            "medical": "102 or 108",
            "women_help": "1091",
            "electricity": "1912 (National Electricity Helpline)",
            "water": "1916 (Municipal Water Supply)",
            "agriculture": "1551 (Kisan Call Center)",
            "scheme": "1076 or 1100 (State CM Helpline)",
            "gas": "1906 (Gas Leak Emergency)",
            "roads": "1073 (Road Accident)",
            "telecom": "198 (Telecom)",
            "general": "1100 or 181"
        }
        active_helpline = HELPLINES.get(department.lower(), "1100 or 181")

        # Build context about ticket or scheme
        ticket_context = f"\\nAssigned Helpline: {active_helpline} (CRITICAL: Tell the user to call this number for immediate help)\\n"
        if db_scheme_data and db_scheme_data.get("found"):
            schemes = [s.get('name', 'Scheme') for s in db_scheme_data.get("raw_results", [])][:3]
            ticket_context += f"\\nRelevant Schemes Found in Database: {', '.join(schemes)}\\n"

        if ticket_number:
            ticket_context += f"\\nTicket Number: {ticket_number} (Please tell user this ticket number)"
        elif is_scheme_enquiry:"""

        if old_context in text:
            text = text.replace(old_context, new_context)
        else:
            print("Warning: old_context not found!")

        # 4. Update Instructions in prompt
        old_instr = """5. For scheme enquiries, provide helpful guidance about where to find scheme information"""
        new_instr = """5. For scheme enquiries, inform them about actual relevant schemes found in the Database Context (if any are listed).
6. ALWAYS state the specific Assigned Helpline number aloud clearly so they know exactly who to call."""

        if old_instr in text:
            text = text.replace(old_instr, new_instr)
        else:
            print("Warning: old_instr not found!")

        # 5. Inject DB Scheme Data before calling groq
        call_target_old = """    groq_response = await generate_groq_response(
        transcript_native,
        lang_code,
        urgency_level,
        analytical_model.intent.primary_intent,
        service_mapped,
        vulgarity_result=vulgarity_result,
        ticket_number=ticket_number,
        is_scheme_enquiry=is_scheme_enquiry,
        state_code=state_code
    )"""
                
        call_target_new = """    # Fetch DB Schemes Dynamically
    db_scheme_data = None
    if is_scheme_enquiry and scheme_classification:
        if isinstance(scheme_classification, dict):
            print(f"  🔍 Querying Neon Database for exact schemes matching domains...")
            try:
                db_scheme_data = fetch_schemes_from_neon(
                    domain=scheme_classification.get("domain", []),
                    beneficiary_groups=scheme_classification.get("beneficiary_groups", [])
                )
                if db_scheme_data and db_scheme_data.get("found"):
                    print(f"  ✓ Database match: Found {len(db_scheme_data.get('raw_results', []))} specific schemes via Neon DB.")
            except Exception as e:
                print(f"  ⚠️ Database fetch failed: {e}")

    groq_response = await generate_groq_response(
        transcript_native,
        lang_code,
        urgency_level,
        analytical_model.intent.primary_intent,
        service_mapped,
        vulgarity_result=vulgarity_result,
        ticket_number=ticket_number,
        is_scheme_enquiry=is_scheme_enquiry,
        state_code=state_code,
        department=final_department,
        db_scheme_data=db_scheme_data
    )"""

        if call_target_old in text:
            text = text.replace(call_target_old, call_target_new)
        else:
            print("Warning: call_target_old not found!")

        with open('interactive_voice_to_layer3_integrated.py', 'w') as f:
            f.write(text)

        print("SUCCESS")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
