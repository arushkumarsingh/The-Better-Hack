import openai
import os
import json
import re
import openai # Ensure openai is imported if not already

def extract_personas_usecases(transcript, keyframe_summaries, model="gpt-4o-mini"):
    system_prompt = "You are a product strategist analyzing product demo materials."
    user_prompt = f"""
Based on the provided transcript and keyframe summaries from a product/app demo video, perform the following analysis:

**Instructions:**
1.  Identify the main applications or distinct functional areas of the app demonstrated.
2.  For each application, list the most relevant use cases shown or implied.
3.  Define the likely user personas who would benefit most from this app. For each persona, provide a brief description and list the applications relevant to them.

**Output Format:**
Return ONLY valid JSON matching this structure exactly:
```json
{{
  "applications": ["App Area 1", "App Area 2", ...],
  "use_cases": {{
    "App Area 1": ["Use Case 1.1", "Use Case 1.2", ...],
    "App Area 2": ["Use Case 2.1", ...]
  }},
  "personas": [
    {{
      "name": "Persona Name 1",
      "description": "Brief description of persona 1.",
      "relevant_applications": ["App Area 1", ...]
    }},
    {{
      "name": "Persona Name 2",
      "description": "Brief description of persona 2.",
      "relevant_applications": ["App Area 2", ...]
    }}
  ]
}}
```

**Input Data:**

### Transcript:
{transcript}

### Keyframe Summaries:
{keyframe_summaries}

---
**Analysis Result (JSON only):**
"""
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=800 # Increased slightly for potentially more detailed JSON
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("[WARN] Could not decode JSON directly. Raw response:\n", raw)
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as e:
                print("[ERROR] Regex-extracted JSON failed:", e)
        raise

def select_lucrative_features(transcript, keyframe_summaries, persona, model="gpt-4o-mini"):
    system_prompt = "You are a product strategist identifying high-value features for specific user segments."
    user_prompt = f"""
Given the transcript and keyframe summaries of an app demo, and the specific user persona provided below, analyze the entire app demonstration.

**Instructions:**
1.  Identify the features, workflows, or application sections demonstrated that will be MOST useful and potentially lucrative (e.g., driving adoption, solving key pain points) for the specified persona.
2.  Select the top 3-5 most impactful features/flows.
3.  For each selected feature/flow, provide a concise justification explaining *why* it is particularly valuable for this persona.

**Output Format:**
Return ONLY valid JSON matching this structure exactly:
```json
{{
  "persona": {{ ... persona object as provided ... }},
  "top_features": [
    {{
      "feature": "Feature/Flow Name 1",
      "justification": "Concise reason why this is valuable for the persona."
    }},
    {{
      "feature": "Feature/Flow Name 2",
      "justification": "Concise reason why this is valuable for the persona."
    }},
    ...
  ]
}}
```
**Input Data:**

### Target Persona:
```json
{json.dumps(persona, indent=2)}
```

### Transcript:
{transcript}

### Keyframe Summaries:
{keyframe_summaries}

---
**Top Features Analysis (JSON only):**
"""
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=700 # Adjusted token count
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("[WARN] Could not decode JSON directly. Raw response:\n", raw)
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as e:
                print("[ERROR] Regex-extracted JSON failed:", e)
        raise
