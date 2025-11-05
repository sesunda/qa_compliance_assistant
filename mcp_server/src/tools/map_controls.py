import os
import json
from typing import List, Dict, Any
import requests

from openai import OpenAI
from datetime import datetime, timezone

# A simple mapping tool that reads control_catalog entries via the API database
# and calls OpenAI to propose IM8 domain mappings. This script is intended to be
# run inside the MCP server container or Codespace where OPENAI_API_KEY is set.

# NOTE: this is a standalone script; in production this should be refactored into
# an MCP tool module and use the project's DB session. For demo we will connect
# to the API via an HTTP endpoint or import models directly depending on deployment.

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in environment")
client = OpenAI(api_key=OPENAI_KEY)

# Example prompt template
PROMPT_TEMPLATE = '''
You are given a security control with a title and description, and a list of IM8 Domain Areas.
Your task: choose the best matching IM8 Domain Area code from the list and provide a short rationale.
Return only a JSON object with keys: domain_code, confidence (0-1), rationale.

Control Title: {title}
Control Description: {description}

IM8 Domain Areas:
{domains}

Respond with JSON only.
'''


def map_control(control: Dict[str, Any], domains: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Build domains text
    domains_text = "\n".join([f"{d['code']}: {d['name']} - {d.get('description','')}" for d in domains])
    prompt = PROMPT_TEMPLATE.format(title=control.get('title',''), description=control.get('description',''), domains=domains_text)

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"You are a helpful security classification assistant."},
                  {"role":"user","content":prompt}],
        temperature=0.0,
        max_tokens=200,
    )
    # New client returns structure: resp.choices[0].message.content
    text = resp.choices[0].message.content.strip()
    # Try to parse JSON from the model output
    try:
        parsed = json.loads(text)
    except Exception:
        # try to extract a JSON object embedded in the text
        import re
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                parsed = {"domain_code": None, "confidence": 0.0, "rationale": text}
        else:
            # fallback: return raw text
            parsed = {"domain_code": None, "confidence": 0.0, "rationale": text}
    return parsed


if __name__ == '__main__':
    # Demo runner: read sample controls from controls_sample.json and domains from domains.json
    here = os.path.dirname(__file__)
    sample_path = os.path.join(here, 'controls_sample.json')
    domains_path = os.path.join(here, 'domains.json')

    if not os.path.exists(sample_path) or not os.path.exists(domains_path):
        print('Place sample files controls_sample.json and domains.json next to this script to run a demo.')
        raise SystemExit(1)

    with open(domains_path, 'r') as f:
        domains = json.load(f)
    with open(sample_path, 'r') as f:
        controls = json.load(f)

    results = []
    for c in controls:
        r = map_control(c, domains)
        # attempt to persist proposal to the API
        api_url = os.getenv("API_URL", "http://api:8000")
        endpoint = f"{api_url.rstrip('/')}/control-catalog/propose"
        payload = {
            "external_id": c.get("id"),
            "title": c.get("title"),
            "description": c.get("description"),
            "raw_json": c,
            "proposed_domain_code": r.get("domain_code"),
            "proposed_confidence": r.get("confidence"),
            "mapping_rationale": r.get("rationale"),
        }

        try:
            resp = requests.post(endpoint, json=payload, timeout=10)
            if resp.status_code in (200, 201):
                saved = resp.json()
                results.append({"control": c, "proposal": r, "mapped_at": datetime.now(timezone.utc).isoformat(), "saved": saved})
            else:
                results.append({"control": c, "proposal": r, "mapped_at": datetime.now(timezone.utc).isoformat(), "saved_error": resp.text})
        except Exception as e:
            results.append({"control": c, "proposal": r, "mapped_at": datetime.now(timezone.utc).isoformat(), "saved_error": str(e)})
    print(json.dumps(results, indent=2))
