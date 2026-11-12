"""
TVCS Whitelist Matcher
----------------------
Cross-references raw company names against the 785 certified TVCS employers in employers_data.json.
Enriches every job with:
- Category (I, II, III, or IV)
- Priority_Tier (1, 2, 3, or 4)
- Priority_Label
- Plaza_Location
- Phone Number
"""

import json
import re

class WhitelistMatcher:
    def __init__(self, employers_file='employers_data.json'):
        self.exact_map = {}
        self.clean_map = {}
        self.alias_map = {
            "uf health": "UF Health (The Villages Hospital)",
            "the villages hospital": "UF Health (The Villages Hospital)",
            "centerwell": "The Villages Health / CenterWell",
            "the villages health": "The Villages Health / CenterWell",
            "tvcs": "The Villages Charter School",
            "the villages charter school": "The Villages Charter School",
            "holding company": "The Villages Operating Entities",
            "the villages of lake-sumter": "The Villages Operating Entities",
            "vccdd": "Village Center Community Dev. District",
            "district gov": "Village Center Community Dev. District",
            "wildwood": "City of Wildwood",
            "lssc": "Lake-Sumter State College",
            "lake sumter state college": "Lake-Sumter State College",
            "sumter county": "Sumter County BOCC",
            "seacoast": "Seacoast National Bank",
            "citizens first": "Seacoast National Bank",
            "jacobs": "Jacobs Engineering & Utilities",
            "4 rivers": "4 Rivers Smokehouse",
            "city fire": "City Fire American Oven & Bar",
            "fmk": "Bluefin Grill and Bar",
            "down to earth": "Down To Earth Landscaping",
            "dte": "Down To Earth Landscaping",
            "florida cancer": "Florida Cancer Specialists",
            "quest diagnostics": "Quest Diagnostics Southern Trace",
            "united health": "United Health Group Brownwood"
        }
        self.tier_map = {
            'CATEGORY I': 1,
            'CATEGORY II': 2,
            'CATEGORY III': 3,
            'CATEGORY IV': 4
        }
        self.load_employers(employers_file)

    def clean_name(self, name):
        if not name:
            return ""
        s = name.lower()
        s = re.sub(r'[\,\.\-\_\(\)\/]', ' ', s)
        s = re.sub(r'\b(inc|llc|corp|ltd|co|pa|group|holdings|services)\b', '', s)
        return re.sub(r'\s+', ' ', s).strip()

    def load_employers(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                employers = json.load(f)
                for emp in employers:
                    c_name = emp['Company']
                    self.exact_map[c_name.lower()] = emp
                    cleaned = self.clean_name(c_name)
                    if cleaned:
                        self.clean_map[cleaned] = emp
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")

    def match(self, raw_company_name):
        """Matches a raw company name to the official TVCS employer profile."""
        if not raw_company_name:
            return self._default_match(raw_company_name)

        raw_lower = raw_company_name.lower().strip()

        # 1. Exact match
        if raw_lower in self.exact_map:
            return self._format_result(self.exact_map[raw_lower], self.exact_map[raw_lower]['Company'])

        # 2. Alias match
        for alias, canonical in self.alias_map.items():
            if alias in raw_lower:
                if canonical.lower() in self.exact_map:
                    return self._format_result(self.exact_map[canonical.lower()], canonical)
                cleaned = self.clean_name(canonical)
                if cleaned in self.clean_map:
                    return self._format_result(self.clean_map[cleaned], canonical)

        # 3. Clean token match
        cleaned_raw = self.clean_name(raw_company_name)
        if cleaned_raw in self.clean_map:
            return self._format_result(self.clean_map[cleaned_raw], self.clean_map[cleaned_raw]['Company'])

        # 4. Substring match
        for clean_key, emp in self.clean_map.items():
            if len(clean_key) >= 4 and (clean_key in cleaned_raw or cleaned_raw in clean_key):
                return self._format_result(emp, emp['Company'])

        return self._default_match(raw_company_name)

    def _format_result(self, emp, canonical_name):
        cat = emp.get('Category', 'CATEGORY III')
        tier = self.tier_map.get(cat, 3)
        priority_label = emp.get('Priority_Label') or f"{cat.title()} (Partner)"
        plaza = emp.get('Plaza') or emp.get('Plaza_Location') or 'The Villages Commercial Area'
        phone = emp.get('Phone') or '(352) 753-6655'

        return {
            "matched": True,
            "canonical_company": canonical_name,
            "Category": cat,
            "Priority_Tier": tier,
            "Priority_Label": priority_label,
            "Plaza_Location": plaza,
            "Phone": phone,
            "TVCS_Qualifying": True
        }

    def _default_match(self, raw_company_name):
        return {
            "matched": False,
            "canonical_company": raw_company_name or "Approved Villages Business",
            "Category": "CATEGORY III",
            "Priority_Tier": 3,
            "Priority_Label": "Category III (Commercial Tenant)",
            "Plaza_Location": "The Villages Commercial Area",
            "Phone": "(352) 753-6655",
            "TVCS_Qualifying": True
        }

if __name__ == '__main__':
    matcher = WhitelistMatcher()
    test_cases = [
        "UF Health",
        "The Villages Health",
        "Down To Earth",
        "FMK Hospitality",
        "Citizens First Bank",
        "Jacobs",
        "City of Wildwood",
        "4 Rivers"
    ]
    print("Testing Whitelist Matcher:")
    for t in test_cases:
        res = matcher.match(t)
        print(f"  '{t}' -> Matched: {res['matched']} | Canonical: '{res['canonical_company']}' | {res['Category']} (Tier {res['Priority_Tier']}) | Plaza: {res['Plaza_Location']}")
