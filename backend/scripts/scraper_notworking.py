# backend/scripts/scraper_final_v8.py
"""
Strategy:
1. Intercept the browser's own API responses (not fetch, not replay)
2. Use page.evaluate to trigger pagination by modifying the URL params
3. The page's own JS makes the API calls — we just read the responses
"""
import os, re, json, time
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PAGE_SIZE = 10


def get_db_url():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return None
    url = re.sub(r"^postgresql\+[\w]+://", "postgresql://", url)
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def main():
    print("🇮🇳 MyScheme Scraper v8 — response interception")
    print("━" * 65)
    t0 = time.time()

    all_search_responses = []
    all_detail_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = context.new_page()

        # ━━━━ Intercept ALL API responses ━━━━
        def on_response(response):
            url = response.url
            try:
                if response.status != 200:
                    return
                ct = response.headers.get("content-type", "")
                if "json" not in ct:
                    return

                # Use response.body() then parse — more reliable than .json()
                raw_body = response.body()
                body = json.loads(raw_body)

                if "search/v6/schemes" in url:
                    all_search_responses.append(body)
                elif "schemes/v6/public" in url:
                    all_detail_responses.append({
                        "url": url,
                        "data": body
                    })
            except Exception:
                pass

        page.on("response", on_response)

        # ━━━━ Step 1: Load search page ━━━━
        print("🌐 Loading search page...")
        page.goto(
            "https://www.myscheme.gov.in/search",
            wait_until="networkidle",
            timeout=60000,
        )
        page.wait_for_timeout(8000)

        print(f"  📡 Captured {len(all_search_responses)} search responses so far")

        # Check first search response
        if all_search_responses:
            first = all_search_responses[0]
            total = find_total(first)
            print(f"  📊 Total schemes: {total}")
            schemes, path = find_schemes(first)
            if schemes:
                print(f"  🎯 Found {len(schemes)} schemes at {path}")
                print(f"  🎯 Keys: {list(schemes[0].keys())[:8]}")
            else:
                print(f"  ❌ Could not parse scheme array from response")
                print(f"  Top keys: {list(first.keys()) if isinstance(first, dict) else type(first)}")
                debug_structure(first)
        else:
            print("  ⚠️  No search responses captured yet")
            total = None

        # ━━━━ Step 2: Paginate by navigating with query params ━━━━
        print(f"\n{'=' * 65}")
        print("📋 STEP 1: Paginating through all schemes")
        print("=" * 65)

        if total and total > PAGE_SIZE:
            pages_needed = (total // PAGE_SIZE) + 1
            print(f"  Need ~{pages_needed} pages of {PAGE_SIZE}")

            for pg_num in range(1, pages_needed + 1):
                offset = pg_num * PAGE_SIZE
                count_before = len(all_search_responses)

                # Navigate to search page with different offset
                # The site uses URL query params or we trigger via JS
                url = (
                    f"https://www.myscheme.gov.in/search"
                    f"?lang=en&from={offset}&size={PAGE_SIZE}"
                )
                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(3000)
                except Exception as e:
                    print(f"  ❌ Navigation error at page {pg_num}: {e}")
                    continue

                new_responses = len(all_search_responses) - count_before
                if new_responses == 0:
                    # The URL params might not work — try JS approach
                    # Trigger the API call via the page's own search mechanism
                    pass

                total_schemes = sum(
                    len(find_schemes(r)[0] or [])
                    for r in all_search_responses
                )

                if pg_num % 10 == 0 or pg_num <= 3:
                    print(
                        f"  Page {pg_num:>4}/{pages_needed} | "
                        f"responses={len(all_search_responses)} | "
                        f"schemes≈{total_schemes}"
                    )

                if total_schemes >= total:
                    print(f"  ✅ Got all {total} schemes")
                    break

                time.sleep(0.5)

        # ━━━━ Collect all unique schemes from captured responses ━━━━
        all_schemes = []
        seen = set()

        for resp_data in all_search_responses:
            items, _ = find_schemes(resp_data)
            if not items:
                continue
            for item in items:
                slug = item.get("slug") or item.get("schemeId") or ""
                if slug and slug not in seen:
                    seen.add(slug)
                    all_schemes.append(item)

        print(f"\n  ✅ Total unique schemes: {len(all_schemes)}")

        # ━━━━ Step 3: Get details by visiting each scheme page ━━━━
        print(f"\n{'=' * 65}")
        print(f"📄 STEP 2: Visiting {len(all_schemes)} scheme pages for details")
        print("=" * 65)

        # Resume support
        progress_path = os.path.join(SCRIPT_DIR, "details_progress.json")
        results = []
        done = set()

        if os.path.exists(progress_path):
            with open(progress_path, encoding="utf-8") as f:
                results = json.load(f)
            done = {r.get("slug", "") for r in results}
            print(f"  📂 Resuming: {len(done)} already done\n")

        detail_responses_before = len(all_detail_responses)
        errors = 0

        for i, scheme in enumerate(all_schemes, 1):
            slug = scheme.get("slug") or scheme.get("schemeId") or ""
            if not slug or slug in done:
                continue

            merged = {**scheme, "slug": slug}
            detail_responses_before = len(all_detail_responses)

            try:
                page.goto(
                    f"https://www.myscheme.gov.in/schemes/{slug}",
                    wait_until="networkidle",
                    timeout=20000,
                )
                page.wait_for_timeout(2000)

                # Check if we got a detail API response
                new_details = all_detail_responses[detail_responses_before:]
                for d in new_details:
                    if slug in d.get("url", ""):
                        merged["detail"] = d["data"]
                        break

                # Also extract from the page itself
                if "detail" not in merged:
                    page_data = page.evaluate("""() => {
                        const r = {};
                        const h1 = document.querySelector('h1');
                        r.title = h1 ? h1.textContent.trim() : '';

                        // Try __NEXT_DATA__
                        const nd = document.getElementById('__NEXT_DATA__');
                        if (nd) {
                            try { r.nextData = JSON.parse(nd.textContent); }
                            catch(e) {}
                        }

                        // Sections
                        const sections = {};
                        document.querySelectorAll('h2, h3').forEach(h => {
                            const key = h.textContent.trim();
                            let txt = '';
                            let sib = h.nextElementSibling;
                            while (sib && !['H2','H3'].includes(sib.tagName)) {
                                txt += sib.innerText + '\\n';
                                sib = sib.nextElementSibling;
                            }
                            if (txt.trim()) sections[key] = txt.trim();
                        });
                        r.sections = sections;

                        const main = document.querySelector('main');
                        r.fullText = main
                            ? main.innerText.substring(0, 10000)
                            : '';

                        return r;
                    }""")

                    # Check __NEXT_DATA__ for scheme details
                    next_data = page_data.get("nextData")
                    if next_data:
                        detail_from_next, _ = find_scheme_detail(next_data)
                        if detail_from_next:
                            merged["detail"] = detail_from_next

                    merged["page_sections"] = page_data.get("sections", {})
                    merged["page_title"] = page_data.get("title", "")
                    merged["full_text"] = page_data.get("fullText", "")

            except Exception as e:
                errors += 1
                merged["detail_error"] = str(e)

            results.append(merged)
            done.add(slug)

            if len(done) % 50 == 0 or i == len(all_schemes):
                name = (
                    scheme.get("schemeShortTitle")
                    or scheme.get("schemeName")
                    or slug
                )
                ok = sum(1 for r in results if "detail" in r or "page_sections" in r)
                print(
                    f"  [{len(done):>5}/{len(all_schemes)}] "
                    f"ok={ok} err={errors} | {name[:55]}"
                )
                with open(progress_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False)

            time.sleep(0.3)

        browser.close()

    # Save final
    final_path = os.path.join(SCRIPT_DIR, "all_schemes_with_details.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results if "detail" in r or "page_sections" in r)
    print(f"\n💾 {len(results)} schemes → {final_path}")
    print(f"✅ With data: {ok} | ❌ Errors: {errors}")

    # Store in Neon
    store_in_neon(results)

    elapsed = time.time() - t0
    print(f"\n⏱️  Done in {elapsed:.0f}s ({elapsed / 60:.1f} min)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def find_schemes(data, path="root"):
    KEYS = {"slug", "schemeId", "schemeName", "schemeShortTitle"}
    if isinstance(data, list) and data and isinstance(data[0], dict):
        if KEYS & set(data[0].keys()):
            return data, path
    if isinstance(data, dict):
        for k, v in data.items():
            r, p = find_schemes(v, f"{path}.{k}")
            if r is not None:
                return r, p
    if isinstance(data, list):
        for i, item in enumerate(data):
            r, p = find_schemes(item, f"{path}[{i}]")
            if r is not None:
                return r, p
    return None, None


def find_scheme_detail(data, path="root"):
    """Find a dict with scheme detail keys inside __NEXT_DATA__"""
    DETAIL_KEYS = {"schemeContent", "schemeBenefits", "schemeEligibility",
                   "briefDescription", "detailedDescription"}
    if isinstance(data, dict):
        if DETAIL_KEYS & set(data.keys()):
            return data, path
        for k, v in data.items():
            r, p = find_scheme_detail(v, f"{path}.{k}")
            if r is not None:
                return r, p
    if isinstance(data, list):
        for i, item in enumerate(data):
            r, p = find_scheme_detail(item, f"{path}[{i}]")
            if r is not None:
                return r, p
    return None, None


def find_total(data):
    if isinstance(data, dict):
        for k in ["total", "totalCount", "count"]:
            v = data.get(k)
            if isinstance(v, (int, float)):
                return int(v)
        for v in data.values():
            r = find_total(v)
            if r is not None:
                return r
    return None


def debug_structure(data, indent=0, max_d=3):
    pfx = "     " + "  " * indent
    if indent >= max_d:
        return
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                print(f"{pfx}{k}: dict({len(v)})")
                debug_structure(v, indent + 1, max_d)
            elif isinstance(v, list):
                t = type(v[0]).__name__ if v else "empty"
                print(f"{pfx}{k}: list({len(v)} × {t})")
                if v and isinstance(v[0], dict):
                    print(f"{pfx}  keys: {list(v[0].keys())[:8]}")
            else:
                print(f"{pfx}{k}: {type(v).__name__} = {str(v)[:60]}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Parse + Store
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def parse_for_db(raw):
    detail = raw.get("detail", {})
    sections = raw.get("page_sections", {})
    inner = detail
    for key in ["data", "en", "schemeContent"]:
        if isinstance(inner, dict) and key in inner:
            inner = inner[key]

    def get(*keys, default=""):
        for src in [inner, raw, detail]:
            if not isinstance(src, dict):
                continue
            for k in keys:
                v = src.get(k)
                if v:
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                    if isinstance(v, list):
                        parts = []
                        for x in v:
                            if isinstance(x, str):
                                parts.append(x)
                            elif isinstance(x, dict):
                                parts.append(
                                    x.get("value") or x.get("text")
                                    or x.get("description")
                                    or json.dumps(x, ensure_ascii=False)
                                )
                        return "\n".join(parts)
        # Try page sections
        for k in keys:
            for sk, sv in sections.items():
                if k.lower() in sk.lower():
                    return sv
        return default

    def get_list(*keys):
        for src in [inner, raw, detail]:
            if not isinstance(src, dict):
                continue
            for k in keys:
                v = src.get(k)
                if isinstance(v, list):
                    return [str(x).strip()[:500] for x in v if x]
        return []

    name = get("schemeShortTitle", "schemeName", "title",
               "page_title", default="Unknown")
    slug = raw.get("slug") or raw.get("schemeId") or ""
    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "unknown"

    description = get("briefDescription", "description",
                      "detailedDescription")
    if not description:
        description = raw.get("full_text", "")[:5000]

    return {
        "scheme_name": name[:500],
        "scheme_slug": slug[:200],
        "ministry": get("nodalMinistryName", "ministryName")[:300],
        "department": get("nodalDepartmentName", "departmentName")[:300],
        "description": description[:15000],
        "benefits": get("benefits", "schemeBenefits", "Benefits")[:15000],
        "eligibility": get("eligibility", "schemeEligibility",
                           "Eligibility")[:15000],
        "application_process": get("applicationProcess", "howToApply",
                                   "Application Process",
                                   "How To Apply")[:15000],
        "documents_required": get_list("documentsRequired", "documents"),
        "scheme_type": get("level", "schemeType", default="central")[:50],
        "target_beneficiaries": get_list("beneficiaries",
                                          "targetBeneficiaries"),
        "state": get("stateName", "implementingState") or None,
        "website_url": f"https://www.myscheme.gov.in/schemes/{slug}",
        "tags": get_list("tags", "categories", "schemeCategory"),
        "source": "myscheme.gov.in",
        "raw_data": raw,
    }


def store_in_neon(items):
    db_url = get_db_url()
    if not db_url:
        print("❌ DATABASE_URL not set. Skipping DB.")
        return

    print(f"\n{'=' * 65}")
    print(f"💾 STEP 3: Storing {len(items)} schemes in Neon DB")
    print("=" * 65)

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


if __name__ == "__main__":
    main()