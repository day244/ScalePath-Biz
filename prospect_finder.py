#!/usr/bin/env python3
"""
ScalePath Startup Prospect Finder Agent
========================================
Finds early-stage startups and their growth/BD leaders for outreach.

Usage:
    python prospect_finder.py
    python prospect_finder.py --regions israel us --max-per-region 15
    python prospect_finder.py --sector SaaS --output my_prospects.csv

Requirements:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key_here
"""

import anthropic
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

DEFAULT_REGIONS = [
    "Israel (Tel Aviv, Jerusalem, Haifa, Herzliya)",
    "United States (Silicon Valley, New York, Austin, Boston, Miami)",
    "Europe (London, Berlin, Amsterdam, Paris, Stockholm, Barcelona)",
]

TARGET_ROLES = [
    "Founder", "Co-Founder", "CEO",
    "Head of Business Development", "VP Business Development",
    "Head of SDR", "Head of Sales Development",
    "Head of Go-to-Market", "GTM Director", "VP Go-to-Market",
    "VP Marketing", "Chief Marketing Officer",
    "VP Sales", "Chief Revenue Officer", "CRO",
    "Head of Partnerships", "Head of Growth",
]

SYSTEM_PROMPT = """You are a startup research specialist for ScalePath.biz, a B2B growth consultancy.

ScalePath helps early-stage startups accelerate their growth through expert lead generation,
market research, and strategic partnerships. Your job is to find ideal prospects who would
benefit from ScalePath's services.

TARGET CRITERIA:
- Companies: Startups founded in 2023 or 2024 (maximum 2 years old)
- Size: 1 to 50 employees
- Geography: Israel, United States, or Europe
- Stage: Seed, Pre-Seed, Series A, or bootstrapped early-stage

TARGET CONTACTS (people most likely to hire a BD consultancy):
- Founders & Co-Founders
- Head of Business Development / VP BD
- Head of SDR (Sales Development Representative)
- Head of Go-to-Market / GTM Director / VP GTM
- VP Marketing / CMO
- VP Sales / CRO
- Head of Partnerships / Head of Growth

SEARCH STRATEGY:
1. Search for recent startup funding news and announcements
2. Look on LinkedIn, Crunchbase, AngelList, ProductHunt, TechCrunch
3. Find the company's team/about page for contact names
4. Verify founding dates and employee counts
5. Look for people recently hired into BD/growth roles

OUTPUT FORMAT — always return valid JSON:
{
  "prospects": [
    {
      "company": "Acme AI",
      "website": "https://acme.ai",
      "founded": "2024",
      "location": "Tel Aviv, Israel",
      "employees": "12",
      "industry": "AI / SaaS",
      "funding_stage": "Seed ($2M)",
      "description": "AI-powered contract management platform for SMBs",
      "source": "TechCrunch, crunchbase.com",
      "contacts": [
        {
          "name": "Sarah Cohen",
          "title": "Co-Founder & CEO",
          "linkedin": "https://linkedin.com/in/sarahcohen",
          "email": ""
        },
        {
          "name": "David Levi",
          "title": "Head of Business Development",
          "linkedin": "https://linkedin.com/in/davidlevi",
          "email": ""
        }
      ]
    }
  ]
}

IMPORTANT:
- Only include real, verifiable companies and people
- Prioritise companies that are actively growing and hiring
- Include LinkedIn URLs whenever you can find them
- Leave fields empty ("") rather than guessing
- Aim for at least 10 prospects per region search
"""


# ── Agent core ────────────────────────────────────────────────────────────────

def extract_json(text: str) -> dict | None:
    """Extract the first valid JSON object from a text string."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON block in markdown code fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Find the outermost { ... } pair
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    break
    return None


def search_region(
    client: anthropic.Anthropic,
    region: str,
    sector: str | None,
    max_results: int,
) -> list[dict]:
    """
    Run one full agentic search for a given region.
    Uses Claude Opus 4.6 with web_search + web_fetch tools.
    """
    sector_clause = f" in the {sector} sector" if sector else ""
    roles_list = ", ".join(TARGET_ROLES[:8])  # keep prompt concise

    user_message = f"""Find {max_results}+ startup prospects{sector_clause} based in {region}.

Use these search queries (run them all):
1. site:crunchbase.com "{region.split('(')[0].strip()}" startup 2023 OR 2024 seed
2. "{region.split('(')[0].strip()}" startup "head of business development" OR "VP sales" 2024
3. "{region.split('(')[0].strip()}" startup founder 2023 2024 "go-to-market" OR "GTM"
4. TechCrunch OR TechEU funding "{region.split('(')[0].strip()}" startup 2024
5. site:linkedin.com "{region.split('(')[0].strip()}" startup "head of SDR" OR "VP marketing" 2024
6. ProductHunt OR AngelList "{region.split('(')[0].strip()}" startup 2023 2024

For each startup found, also search for their team page to get contact names and titles.

Requirements:
- Founded 2023 or 2024 only
- 1–50 employees
- Include at least one growth/BD contact per company (roles: {roles_list})

Return all results as a single JSON object following the exact schema in your instructions."""

    messages = [{"role": "user", "content": user_message}]
    prospects: list[dict] = []

    print(f"\n  Running agentic search (this may take 1-3 minutes)...")

    # Agentic loop — Claude may call web_search/web_fetch multiple times
    iteration = 0
    max_iterations = 20  # safety cap

    while iteration < max_iterations:
        iteration += 1
        sys.stdout.write(f"\r  Iteration {iteration:2d} — querying Claude...")
        sys.stdout.flush()

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=SYSTEM_PROMPT,
            tools=[
                {"type": "web_search_20260209", "name": "web_search"},
                {"type": "web_fetch_20260209", "name": "web_fetch"},
            ],
            messages=messages,
        )

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Collect all text blocks and try to parse JSON
            full_text = "\n".join(
                block.text
                for block in response.content
                if hasattr(block, "text")
            )
            parsed = extract_json(full_text)
            if parsed:
                prospects = parsed.get("prospects", [])
            else:
                # Fallback: store raw text for review
                prospects = [{"raw_response": full_text, "region": region}]
            break

        if response.stop_reason == "tool_use":
            # Execute all tool calls and feed results back
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    sys.stdout.write(
                        f"\r  Iteration {iteration:2d} — {block.name}: {str(block.input)[:60]}..."
                    )
                    sys.stdout.flush()
                    # The API executes the search server-side; we just relay the result
                    # (For web_search / web_fetch, the result comes back in the next turn)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "Tool executed — results will be returned by the API.",
                        }
                    )
            # NOTE: With server-side tools (web_search / web_fetch), the API fills
            # the tool results itself. We must NOT add a tool_result message;
            # instead we re-send and let Claude continue.
            # Remove the fake tool_results we built above.
            # The pattern for server-side tools is: re-send with the assistant turn appended.
            continue  # next iteration will send the growing messages list

        # pause_turn — re-send to continue
        if response.stop_reason == "pause_turn":
            continue

        # Unexpected stop
        break

    print()  # newline after progress line
    return prospects


# ── Output ────────────────────────────────────────────────────────────────────

def flatten_to_rows(prospects: list[dict]) -> list[dict]:
    """One row per contact (multiple rows per company if multiple contacts)."""
    rows = []
    for p in prospects:
        if "raw_response" in p:
            continue  # skip unstructured fallback entries
        base = {
            "Company":       p.get("company", ""),
            "Website":       p.get("website", ""),
            "Founded":       p.get("founded", ""),
            "Location":      p.get("location", ""),
            "Employees":     p.get("employees", ""),
            "Industry":      p.get("industry", ""),
            "Funding Stage": p.get("funding_stage", ""),
            "Description":   p.get("description", ""),
            "Source":        p.get("source", ""),
        }
        contacts = p.get("contacts") or [{}]
        for c in contacts:
            row = dict(base)
            row["Contact Name"]  = c.get("name", "")
            row["Contact Title"] = c.get("title", "")
            row["LinkedIn"]      = c.get("linkedin", "")
            row["Email"]         = c.get("email", "")
            rows.append(row)
    return rows


CSV_FIELDS = [
    "Company", "Website", "Founded", "Location", "Employees",
    "Industry", "Funding Stage", "Description", "Source",
    "Contact Name", "Contact Title", "LinkedIn", "Email",
]


def save_csv(rows: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_json(data: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def print_summary(prospects: list[dict]) -> None:
    print("\n" + "─" * 60)
    print("RESULTS SUMMARY")
    print("─" * 60)
    for p in prospects:
        if "raw_response" in p:
            print(f"  ⚠  Unstructured result for {p.get('region', '?')}")
            continue
        contacts = p.get("contacts", [])
        contact_str = ", ".join(
            f"{c.get('name','?')} ({c.get('title','?')})" for c in contacts[:2]
        )
        if len(contacts) > 2:
            contact_str += f" +{len(contacts)-2} more"
        print(f"  ✓ {p.get('company','?'):30s}  {p.get('location',''):25s}  {contact_str}")
    print("─" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ScalePath Startup Prospect Finder — powered by Claude Opus 4.6"
    )
    parser.add_argument(
        "--regions",
        nargs="+",
        choices=["israel", "us", "europe"],
        default=["israel", "us", "europe"],
        help="Regions to search (default: all three)",
    )
    parser.add_argument(
        "--sector",
        type=str,
        default=None,
        help="Optional sector filter e.g. 'SaaS', 'FinTech', 'AI'",
    )
    parser.add_argument(
        "--max-per-region",
        type=int,
        default=15,
        metavar="N",
        help="Target number of prospects per region (default: 15)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="CSV output filename (default: prospects_TIMESTAMP.csv)",
    )
    return parser.parse_args()


REGION_MAP = {
    "israel": "Israel (Tel Aviv, Jerusalem, Haifa, Herzliya)",
    "us":     "United States (Silicon Valley, New York, Austin, Boston, Miami)",
    "europe": "Europe (London, Berlin, Amsterdam, Paris, Stockholm, Barcelona)",
}


def main() -> None:
    args = parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.")
        print("       Export it with:  export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path  = Path(args.output) if args.output else Path(f"prospects_{timestamp}.csv")
    json_path = Path(f"prospects_{timestamp}.json")

    print("=" * 60)
    print("  ScalePath Startup Prospect Finder")
    print("  Powered by Claude Opus 4.6 + Web Search")
    print("=" * 60)
    print(f"  Regions  : {', '.join(args.regions)}")
    print(f"  Sector   : {args.sector or 'All sectors'}")
    print(f"  Target   : {args.max_per_region} prospects / region")
    print(f"  Output   : {csv_path}")
    print("=" * 60)

    all_prospects: list[dict] = []

    for region_key in args.regions:
        region_label = REGION_MAP[region_key]
        print(f"\n🌍 Searching: {region_label}")
        try:
            prospects = search_region(
                client=client,
                region=region_label,
                sector=args.sector,
                max_results=args.max_per_region,
            )
            print(f"  ✅ Found {len(prospects)} prospect(s)")
            all_prospects.extend(prospects)
        except anthropic.APIError as e:
            print(f"  ❌ API error for {region_label}: {e}")
        except Exception as e:
            print(f"  ❌ Unexpected error for {region_label}: {e}")
            raise

    # Display summary
    structured = [p for p in all_prospects if "raw_response" not in p]
    print_summary(structured)

    # Save outputs
    rows = flatten_to_rows(all_prospects)
    if rows:
        save_csv(rows, csv_path)
        print(f"\n📊 CSV  → {csv_path}  ({len(rows)} rows)")
    else:
        print("\n⚠  No structured prospects to save to CSV.")

    save_json(all_prospects, json_path)
    print(f"📦 JSON → {json_path}  ({len(all_prospects)} companies)")

    raw_count = len(all_prospects) - len(structured)
    if raw_count:
        print(f"\n⚠  {raw_count} region(s) returned unstructured data.")
        print(f"   Check the JSON file for raw content.")

    print("\n✨ Done! Open the CSV in Excel / Google Sheets for outreach.\n")


if __name__ == "__main__":
    main()
