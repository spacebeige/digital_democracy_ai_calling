# backend/scripts/scraper_schemeseva_fixed.py
"""
Fixed version:
1. Handles API 500 errors by reducing page size
2. Trims raw_data to avoid Neon connection drops
3. Reconnects to DB on failure
4. Resumes from saved JSON if re-run
"""
import os, re, json, time
from curl_cffi import requests as curl_requests
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

API_ALL    = "https://scheme-seva-backend.vercel.app/api/v2/schemes/get-all-schemes"
FRONTEND   = "https://scheme-seva-gov.vercel.app"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_FILE  = os.path.join(SCRIPT_DIR, "all_schemes_list.json")

HEADERS = {
    "Referer": f"{FRONTEND}/",
    "Origin": FRONTEND,
}


def get_db_url():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return None
    url = re.sub(r"^postgresql\+[\w]+://", "postgresql://", url)
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def extract_text(blocks):
    if isinstance(blocks, str):
        return blocks
    if not isinstance(blocks, list):
        return ""
    parts = []
    for block in blocks:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            if block.get("text"):
                parts.append(block["text"])
            if block.get("process_md"):
                parts.append(block["process_md"])
            for key in ["children", "process"]:
                if key in block:
                    parts.append(extract_text(block[key]))
    return "\n".join(p for p in parts if p and p.strip())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 1: Fetch all schemes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_all():
    # Resume from file if exists
    if os.path.exists(LIST_FILE):
        with open(LIST_FILE, encoding="utf-8") as f:
            existing = json.load(f)
        if len(existing) > 0:
            print(f"📂 Found {len(existing)} schemes in {LIST_FILE}")
            choice = input("   Use existing? (y/n): ").strip().lower()
            if choice == "y":
                return existing

    print("=" * 60)
    print("📋 STEP 1: Fetching all schemes")
    print("=" * 60)

    all_schemes = []
    seen = set()
    pg = 1
    page_size = 50
    total_pages = None
    consecutive_errors = 0

    while True:
        try:
            resp = curl_requests.get(
                f"{API_ALL}?page={pg}&limit={page_size}",
                impersonate="chrome",
                headers=HEADERS,
                timeout=30,
            )
        except Exception as e:
            consecutive_errors += 1
            print(f"  ❌ Network error page {pg}: {str(e)[:80]}")
            if consecutive_errors >= 3:
                # Wait longer
                print(f"  ⏳ Waiting 30s before retry...")
                time.sleep(30)
                consecutive_errors = 0
            else:
                time.sleep(5)
            continue

        if resp.status_code == 429:
            print(f"  ⏳ Rate limited. Sleeping 15s...")
            time.sleep(15)
            continue

        if resp.status_code == 500:
            # MongoDB sort memory error — reduce page size
            if page_size > 10:
                page_size = 10
                print(f"  ⚠️  Server error. Reducing page size to {page_size}")
                continue
            else:
                print(f"  ❌ Server error even with size={page_size}. Skipping page {pg}.")
                pg += 1
                continue

        if resp.status_code != 200:
            print(f"  ❌ Status {resp.status_code} page {pg}: {resp.text[:100]}")
            consecutive_errors += 1
            if consecutive_errors >= 5:
                print(f"  ❌ Too many errors. Stopping.")
                break
            time.sleep(5)
            continue

        consecutive_errors = 0
        data = resp.json()

        if pg == 1 or total_pages is None:
            total_schemes = data.get("totalSchemes", data.get("total", "?"))
            total_pages = data.get("totalPages", "?")
            if total_pages != "?" and page_size != 50:
                # Recalculate total pages for smaller page size
                total_pages = (int(total_schemes) // page_size) + 1
            print(f"  📊 Total: {total_schemes} schemes, ~{total_pages} pages (size={page_size})")

        schemes = data.get("schemes", [])
        if not schemes:
            print(f"  ⚠️  Empty page {pg}. Done.")
            break

        new = 0
        for s in schemes:
            sid = s.get("_id", "")
            if sid and sid not in seen:
                seen.add(sid)
                all_schemes.append(s)
                new += 1

        print(
            f"  Page {pg:>4} | size={page_size:>2} | "
            f"got={len(schemes):>3} | new={new:>3} | "
            f"total={len(all_schemes)}"
        )

        # Save progress every 10 pages
        if pg % 10 == 0:
            with open(LIST_FILE, "w", encoding="utf-8") as f:
                json.dump(all_schemes, f, ensure_ascii=False)

        if new == 0:
            break
        if total_pages != "?" and pg >= total_pages:
            print(f"  ✅ Last page")
            break

        pg += 1
        time.sleep(0.4)

    # Final save
    with open(LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(all_schemes, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 {len(all_schemes)} schemes → {LIST_FILE}")

    return all_schemes


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 2: Parse for DB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def parse_for_db(raw):
    def get_str(*keys, default=""):
        for k in keys:
            v = raw.get(k)
            if not v:
                continue
            if isinstance(v, str) and v.strip():
                return v.strip()
            if isinstance(v, list):
                return extract_text(v)
        return default

    name = get_str("schemeName", "schemeShortTitle", "title", default="Unknown")
    slug = (
        raw.get("schemeShortTitle")
        or raw.get("_id")
        or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    )

    # Application process
    app_text = ""
    ap = raw.get("applicationProcess")
    if isinstance(ap, list):
        for block in ap:
            if isinstance(block, dict):
                mode = block.get("mode", "")
                md = block.get("process_md", "")
                if md:
                    app_text += f"[{mode}]\n{md}\n\n"
                elif block.get("process"):
                    app_text += f"[{mode}]\n{extract_text(block['process'])}\n\n"

    # Documents
    docs = []
    for item in raw.get("documents_required", []):
        t = extract_text([item]) if isinstance(item, dict) else str(item)
        t = t.strip()
        if t:
            docs.append(t[:500])

    # Tags
    tags = list(set(
        str(t).strip()
        for t in (raw.get("tags", []) or []) + (raw.get("category", []) or [])
        if t and str(t).strip()
    ))

    # Description + FAQs
    desc = get_str("detailedDescription_md", "briefDescription", "description")
    faqs = raw.get("faqs", [])
    if isinstance(faqs, list) and faqs:
        faq_parts = []
        for faq in faqs[:10]:
            q = faq.get("question", "")
            a = faq.get("answer", "")
            if q:
                faq_parts.append(f"Q: {q}\nA: {a}")
        if faq_parts:
            desc += "\n\n--- FAQs ---\n\n" + "\n\n".join(faq_parts)

    # Trim raw_data to avoid huge JSONB (remove nested rich content)
    trimmed_raw = {
        "_id": raw.get("_id"),
        "schemeName": raw.get("schemeName"),
        "schemeShortTitle": raw.get("schemeShortTitle"),
        "state": raw.get("state"),
        "level": raw.get("level"),
        "nodalMinistryName": raw.get("nodalMinistryName"),
        "tags": raw.get("tags"),
        "category": raw.get("category"),
        "openDate": raw.get("openDate"),
        "closeDate": raw.get("closeDate"),
        "references": raw.get("references"),
    }

    return {
        "scheme_name": name[:500],
        "scheme_slug": str(slug)[:200],
        "ministry": get_str("nodalMinistryName", "ministryName")[:300],
        "department": "",
        "description": desc[:15000],
        "benefits": get_str("benefits")[:15000],
        "eligibility": get_str("eligibilityDescription_md", "eligibility")[:15000],
        "application_process": app_text[:15000],
        "documents_required": docs,
        "scheme_type": (raw.get("level") or "central")[:50],
        "target_beneficiaries": [],
        "state": raw.get("state") or None,
        "website_url": f"{FRONTEND}/scheme/{raw.get('_id', '')}",
        "tags": tags,
        "source": "schemeseva",
        "raw_data": trimmed_raw,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 3: Store in Neon (with reconnect)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def store_in_neon(items):
    db_url = get_db_url()
    if not db_url:
        print("❌ DATABASE_URL not set. Skipping DB.")
        return

    print(f"\n{'=' * 60}")
    print(f"💾 STEP 3: Storing {len(items)} schemes in Neon DB")
    print("=" * 60)

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schemes (
            id SERIAL PRIMARY KEY,
            scheme_name TEXT NOT NULL,
            scheme_slug TEXT UNIQUE,
            ministry TEXT DEFAULT '',
            department TEXT DEFAULT '',
            description TEXT DEFAULT '',
            benefits TEXT DEFAULT '',
            eligibility TEXT DEFAULT '',
            application_process TEXT DEFAULT '',
            documents_required TEXT[] DEFAULT '{}',
            scheme_type TEXT DEFAULT 'central',
            target_beneficiaries TEXT[] DEFAULT '{}',
            state TEXT,
            website_url TEXT DEFAULT '',
            tags TEXT[] DEFAULT '{}',
            source TEXT DEFAULT '',
            raw_data JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_schemes_slug ON schemes(scheme_slug);
        CREATE INDEX IF NOT EXISTS idx_schemes_state ON schemes(state);
        CREATE INDEX IF NOT EXISTS idx_schemes_tags ON schemes USING GIN(tags);
    """)
    conn.commit()

    inserted = updated = errors = 0
    batch_count = 0

    for raw_item in items:
        parsed = parse_for_db(raw_item)
        if parsed["scheme_slug"] in ("", "unknown"):
            continue
        if parsed["scheme_name"] == "Unknown":
            continue

        try:
            cur.execute("""
                INSERT INTO schemes (
                    scheme_name, scheme_slug, ministry, department,
                    description, benefits, eligibility,
                    application_process, documents_required,
                    scheme_type, target_beneficiaries, state,
                    website_url, tags, source, raw_data
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (scheme_slug) DO UPDATE SET
                    scheme_name = EXCLUDED.scheme_name,
                    ministry = CASE WHEN EXCLUDED.ministry != ''
                                    THEN EXCLUDED.ministry
                                    ELSE schemes.ministry END,
                    description = CASE WHEN EXCLUDED.description != ''
                                       THEN EXCLUDED.description
                                       ELSE schemes.description END,
                    benefits = CASE WHEN EXCLUDED.benefits != ''
                                    THEN EXCLUDED.benefits
                                    ELSE schemes.benefits END,
                    eligibility = CASE WHEN EXCLUDED.eligibility != ''
                                       THEN EXCLUDED.eligibility
                                       ELSE schemes.eligibility END,
                    application_process = CASE WHEN EXCLUDED.application_process != ''
                                               THEN EXCLUDED.application_process
                                               ELSE schemes.application_process END,
                    documents_required = EXCLUDED.documents_required,
                    tags = EXCLUDED.tags,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = NOW()
                RETURNING (xmax = 0)
            """, (
                parsed["scheme_name"], parsed["scheme_slug"],
                parsed["ministry"], parsed["department"],
                parsed["description"], parsed["benefits"],
                parsed["eligibility"], parsed["application_process"],
                parsed["documents_required"] or [],
                parsed["scheme_type"],
                parsed["target_beneficiaries"] or [],
                parsed["state"], parsed["website_url"],
                parsed["tags"] or [], parsed["source"],
                Json(parsed["raw_data"]),
            ))
            row = cur.fetchone()
            if row and row[0]:
                inserted += 1
            else:
                updated += 1

            batch_count += 1
            # Commit every 50 rows
            if batch_count % 50 == 0:
                conn.commit()
                print(f"  💾 Progress: {inserted + updated} done ({inserted} new, {updated} updated)")

        except psycopg2.OperationalError as e:
            # Connection lost — reconnect
            print(f"  ⚠️  Connection lost. Reconnecting...")
            try:
                conn.close()
            except:
                pass
            time.sleep(2)
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            errors += 1

        except Exception as e:
            conn.rollback()
            errors += 1
            if errors <= 5:
                print(f"  ❌ {parsed['scheme_slug'][:30]}: {str(e)[:80]}")

    # Final commit
    try:
        conn.commit()
    except:
        pass

    try:
        cur.close()
        conn.close()
    except:
        pass

    print(f"\n  ✅ Inserted: {inserted}")
    print(f"  🔄 Updated:  {updated}")
    print(f"  ❌ Errors:    {errors}")
    print(f"  📊 Total in DB: {inserted + updated}")


def main():
    print("🇮🇳 SchemeSeva Scraper (Fixed)")
    print("━" * 60)
    t0 = time.time()

    # Test
    print("🧪 Testing API...")
    try:
        r = curl_requests.get(
            f"{API_ALL}?page=1&limit=1",
            impersonate="chrome",
            headers=HEADERS,
            timeout=15,
        )
        print(f"  Status: {r.status_code}")
        if r.status_code != 200:
            print(f"  ❌ {r.text[:200]}")
            return
        d = r.json()
        print(f"  ✅ Works! Total: {d.get('totalSchemes', '?')}")
    except Exception as e:
        print(f"  ❌ {e}")
        return

    # Step 1
    schemes = fetch_all()
    if not schemes:
        print("❌ No schemes!")
        return

    # Step 2
    store_in_neon(schemes)

    elapsed = time.time() - t0
    print(f"\n⏱️  Done in {elapsed:.0f}s ({elapsed / 60:.1f} min)")
    print(f"📊 {len(schemes)} schemes processed!")


if __name__ == "__main__":
    main()