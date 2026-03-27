# backend/scripts/scraper_schemeseva_final.py
"""
Uses curl_cffi to impersonate Chrome TLS fingerprint.
Bypasses bot detection on SchemeSeva backend.
"""
import os, re, json, time
from curl_cffi import requests as curl_requests
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

API_ALL    = "https://scheme-seva-backend.vercel.app/api/v2/schemes/get-all-schemes"
API_DETAIL = "https://scheme-seva-backend.vercel.app/api/v2/schemes/get-scheme-by-id"
FRONTEND   = "https://scheme-seva-gov.vercel.app"
PAGE_SIZE  = 50
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Rich content → plain text
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
#  STEP 1: Paginate
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_all():
    print("=" * 60)
    print("📋 STEP 1: Fetching all schemes")
    print("=" * 60)

    all_schemes = []
    seen = set()
    pg = 1
    total_pages = None

    while True:
        try:
            resp = curl_requests.get(
                f"{API_ALL}?page={pg}&limit={PAGE_SIZE}",
                impersonate="chrome",
                headers=HEADERS,
                timeout=30,
            )
        except Exception as e:
            print(f"  ❌ Network error page {pg}: {e}")
            time.sleep(5)
            continue

        if resp.status_code == 429:
            print(f"  ⏳ Rate limited. Sleeping 10s...")
            time.sleep(10)
            continue

        if resp.status_code != 200:
            print(f"  ❌ Status {resp.status_code} on page {pg}: {resp.text[:150]}")
            break

        data = resp.json()

        if pg == 1:
            total_pages = data.get("totalPages", "?")
            total_count = data.get("totalSchemes", data.get("total", "?"))
            print(f"  📊 Total: {total_count} schemes, {total_pages} pages")

            debug = os.path.join(SCRIPT_DIR, "schemeseva_first.json")
            with open(debug, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  💾 Sample → {debug}")

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
            f"  Page {pg:>3}/{total_pages} | "
            f"got={len(schemes):>3} | new={new:>3} | "
            f"total={len(all_schemes)}"
        )

        if new == 0:
            break
        if total_pages != "?" and pg >= total_pages:
            print(f"  ✅ Last page")
            break

        pg += 1
        time.sleep(0.3)

    out = os.path.join(SCRIPT_DIR, "all_schemes_list.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_schemes, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 {len(all_schemes)} schemes → {out}")

    return all_schemes


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 2: Fetch details (optional)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def fetch_details(schemes):
    print(f"\n{'=' * 60}")
    print(f"📄 STEP 2: Fetching details for {len(schemes)} schemes")
    print("=" * 60)

    first_id = schemes[0].get("_id", "") if schemes else ""
    if not first_id:
        print("  ⚠️  No _id. Skipping.")
        return schemes

    # Test detail endpoint
    try:
        t = curl_requests.get(
            f"{API_DETAIL}/{first_id}",
            impersonate="chrome",
            headers=HEADERS,
            timeout=15,
        )
        if t.status_code != 200:
            print(f"  ⚠️  Detail endpoint returned {t.status_code}. Using list data.")
            return schemes
        print(f"  ✅ Detail endpoint works!")
    except:
        print(f"  ⚠️  Detail endpoint unreachable. Using list data.")
        return schemes

    progress = os.path.join(SCRIPT_DIR, "detail_progress.json")
    results = []
    done = set()

    if os.path.exists(progress):
        with open(progress, encoding="utf-8") as f:
            results = json.load(f)
        done = {r.get("_id", "") for r in results}
        print(f"  📂 Resuming: {len(done)} done")

    errors = 0
    for i, scheme in enumerate(schemes, 1):
        sid = scheme.get("_id", "")
        if not sid or sid in done:
            continue

        try:
            r = curl_requests.get(
                f"{API_DETAIL}/{sid}",
                impersonate="chrome",
                headers=HEADERS,
                timeout=15,
            )
            if r.status_code == 200:
                results.append(r.json())
            elif r.status_code == 429:
                print(f"  ⏳ Rate limit at {i}. Sleeping 10s...")
                time.sleep(10)
                r = curl_requests.get(
                    f"{API_DETAIL}/{sid}",
                    impersonate="chrome",
                    headers=HEADERS,
                    timeout=15,
                )
                results.append(r.json() if r.status_code == 200 else scheme)
                if r.status_code != 200:
                    errors += 1
            else:
                results.append(scheme)
                errors += 1
        except:
            results.append(scheme)
            errors += 1

        done.add(sid)

        if len(done) % 200 == 0 or i == len(schemes):
            name = scheme.get("schemeName", sid)[:50]
            print(f"  [{len(done):>5}/{len(schemes)}] err={errors} | {name}")
            with open(progress, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False)

        time.sleep(0.15)

    out = os.path.join(SCRIPT_DIR, "all_schemes_detailed.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 {len(results)} detailed → {out}")

    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STEP 3: Parse + Store
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
    tags = raw.get("tags", []) or []
    cats = raw.get("category", []) or []
    all_tags = list(set(
        str(t).strip() for t in tags + cats if t and str(t).strip()
    ))

    # Description + FAQs
    desc = get_str("detailedDescription_md", "briefDescription", "description")
    faqs = raw.get("faqs", [])
    if isinstance(faqs, list) and faqs:
        faq_parts = []
        for faq in faqs[:15]:
            q = faq.get("question", "")
            a = faq.get("answer", "")
            if q:
                faq_parts.append(f"Q: {q}\nA: {a}")
        if faq_parts:
            desc += "\n\n--- FAQs ---\n\n" + "\n\n".join(faq_parts)

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
        "tags": all_tags,
        "source": "schemeseva",
        "raw_data": raw,
    }


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
            conn.commit()
        except Exception as e:
            conn.rollback()
            errors += 1
            if errors <= 5:
                print(f"  ❌ {parsed['scheme_slug'][:30]}: {e}")

    cur.close()
    conn.close()
    print(f"  ✅ Inserted: {inserted}")
    print(f"  🔄 Updated:  {updated}")
    print(f"  ❌ Errors:    {errors}")


def main():
    print("🇮🇳 SchemeSeva Scraper (curl_cffi)")
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
        print(f"  ✅ Works! Total: {d.get('totalSchemes', d.get('total', '?'))}")
    except Exception as e:
        print(f"  ❌ {e}")
        return

    schemes = fetch_all()
    if not schemes:
        print("❌ No schemes!")
        return

    # Optional: uncomment for richer data per scheme
    # schemes = fetch_details(schemes)

    store_in_neon(schemes)

    elapsed = time.time() - t0
    print(f"\n⏱️  Done in {elapsed:.0f}s ({elapsed / 60:.1f} min)")
    print(f"📊 {len(schemes)} schemes scraped & stored!")


if __name__ == "__main__":
    main()