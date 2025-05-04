import openai

import os
import json

import re

def generate_folder_structure(transcript, user_journey_flow, model="gpt-4o-mini", language=None):
    prompt = f"""
You are a technical writer. Based on the transcript and the following User Journey Flow, propose a logical folder and markdown file structure for comprehensive documentation. Use nested folders if needed. Output ONLY valid JSON, and nothing else (no explanations, no markdown, no prose). Example: {{"docs": {{"introduction.md": null, "usage": {{"step1.md": null}}}}}}

User Journey Flow:
{user_journey_flow}

Transcript:
{transcript}
"""
    if language and language.lower() != "english":
        prompt += f"\nOutput ONLY in {language}."
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("[WARN] Could not decode JSON directly. Raw response:\n", raw)
        # Try to extract the first JSON object from the response
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception as e:
                print("[ERROR] Regex-extracted JSON failed:", e)
        raise

def generate_markdown_skeletons(folder_structure, user_journey_flow, base_path="output/docs"):
    """
    Recursively creates folders/files and writes skeleton markdowns with section headings and navigation links.
    """
    def recurse(struct, path, parent_nav=None):
        os.makedirs(path, exist_ok=True)
        for name, child in struct.items():
            full_path = os.path.join(path, name)
            if child is None:
                # Write skeleton markdown
                with open(full_path, "w") as f:
                    title = name.replace(".md", "").replace("_", " ").title()
                    f.write(f"# {title}\n\n")
                    f.write(f"<!-- Navigation: {parent_nav or ''} -->\n\n")
                    f.write(f"<!-- Section headings and placeholders based on user journey: {user_journey_flow[:200]}... -->\n\n")
            else:
                recurse(child, full_path, parent_nav=path)
    recurse(folder_structure, base_path)

def populate_markdown_files(folder_structure, transcript, user_journey_flow, base_path="output/docs", model="gpt-4o-mini", language=None):
    """
    For each markdown file in the folder structure, use AI to populate it with detailed content.
    """
    def recurse(struct, path):
        for name, child in struct.items():
            full_path = os.path.join(path, name)
            if child is None:
                # Read skeleton
                with open(full_path, "r") as f:
                    skeleton = f.read()
                prompt = f"""
You are a technical writer. Given the following transcript (with a timestamp for every sentence), user journey flow (with a timestamp for every keyframe summary), and this markdown skeleton, populate the markdown file with detailed, relevant documentation. The user journey flow is provided ONLY for your understanding and context—do NOT include it, reference it, or copy from it in the final documentation. Use the user journey flow and transcript to inform your synthesis, but only write clear, concise, non-repetitive documentation in the markdown file. Do NOT include transcript quotes, explicit transcript lines, or timestamps in the final documentation. Fill in all sections. Cross-reference other docs where appropriate.

User Journey Flow (for your understanding only, do NOT include or reference this in the docs):
{user_journey_flow}

Transcript:
{transcript}

Markdown Skeleton:
{skeleton}
"""
                if language and language.lower() != "english":
                    prompt += f"\nOutput ONLY in {language}."
                response = openai.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800
                )
                with open(full_path, "w") as f:
                    f.write(response.choices[0].message.content)
            else:
                recurse(child, full_path)
    recurse(folder_structure, base_path)

# (Legacy) Single-step doc generator for reference

def generate_markdown(transcript, user_journey_flow):
    prompt = f"""
You are a technical writer. Based on the transcript and the following 'User Journey Flow' (which summarizes the sequence of user actions and application states based on key screenshots), create clear, step-by-step software documentation in markdown.

User Journey Flow:
{user_journey_flow}

Transcript:
{transcript}

Instructions:
- Structure the documentation around the steps in the User Journey Flow.
- For each step, reference relevant transcript details and visual context.
- Use headings, bullet points, and numbered steps for clarity.
"""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
