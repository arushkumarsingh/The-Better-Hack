import openai
import os
import json
import re

def extract_personas_usecases(transcript, keyframe_summaries, model="gpt-4o-mini"):
    prompt = f"""
You are a product strategist. Based on the transcript and keyframe summaries from a product/app demo video, extract:
1. The main applications of the app.
2. The most relevant use cases for each application.
3. The user personas who would benefit from this app, with a brief description for each persona.

Return ONLY valid JSON of the form:
{"applications": [...], "use_cases": {"application": ["use_case1", ...]}, "personas": [{"name": ..., "description": ..., "relevant_applications": [...]}]}

Transcript:
{transcript}

Keyframe Summaries:
{keyframe_summaries}
"""
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
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
    prompt = f"""
You are a product strategist. Given the transcript and keyframe summaries of an app demo, and a specific user persona, analyze the entire app and select the features, flows, or sections that will be MOST useful and lucrative for this persona. For each, provide a short justification. Return ONLY valid JSON of the form:
{"persona": ..., "top_features": [{"feature": ..., "justification": ...}]}

Persona:
{persona}

Transcript:
{transcript}

Keyframe Summaries:
{keyframe_summaries}
"""
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600
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
