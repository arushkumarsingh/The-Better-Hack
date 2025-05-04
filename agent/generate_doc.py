import openai

import os
import json

import re
from pathlib import Path
import openai # Ensure openai is imported

def generate_folder_structure(transcript, user_journey_flow, model="gpt-4o-mini", language=None):
    system_prompt = "You are an expert documentation architect specializing in creating logical, outcome-oriented information structures."
    user_prompt = f"""
Based on the provided User Journey Flow and Transcript from a product demo, propose a logical folder and markdown file structure for a practical 'how-to' guide.

**Goal:** Design a structure that helps users easily find information to achieve specific goals and understand use cases demonstrated in the video.

**Requirements:**
1.  The structure should reflect the logical flow of the user journey.
2.  Use clear, descriptive names for folders and files (e.g., `getting_started/`, `core_features/feature_a.md`).
3.  Use nested folders where appropriate for organization.
4.  The output MUST be ONLY a valid JSON object representing the structure. Keys are folder/file names. Values are nested objects for folders or `null` for files.

**Output Format Example:**
```json
{{
  "docs": {{
    "introduction.md": null,
    "getting_started": {{
      "installation.md": null,
      "first_steps.md": null
    }},
    "main_feature_a": {{
      "overview.md": null,
      "how_to_use_a.md": null
    }},
    "troubleshooting.md": null
  }}
}}
```
{f'**Language:** Generate all folder and file names ONLY in {language}.' if language and language.lower() != "english" else ''}

**Input Data:**

### User Journey Flow:
{user_journey_flow}

### Transcript:
{transcript}

---
**Proposed Folder Structure (JSON only):**
"""
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=600 # Increased slightly for potentially deeper structures
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
        Path(path).mkdir(parents=True, exist_ok=True)

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
                system_prompt = "You are a practical documentation writer, skilled at creating clear, outcome-oriented how-to guides based on provided context."
                user_prompt = f"""
Your task is to write the content for a specific section of a documentation guide, based on the provided User Journey Flow, Transcript, and the Markdown Skeleton for this section.

**Goal:** Create an easy-to-follow, practical guide for the user actions covered in this section.

**Instructions:**
1.  Focus on user goals, real-world use cases, and actionable step-by-step instructions relevant to this specific section (indicated by the skeleton).
2.  Use the User Journey Flow and Transcript as primary sources for the steps and outcomes.
3.  Populate the provided Markdown Skeleton with detailed content.
4.  **Markdown Formatting:**
    *   Adhere strictly to **CommonMark** Markdown syntax.
    *   Use standard headings (`#`, `##`, `###`, etc.), ensuring correct hierarchy.
    *   Use standard lists (`-` or `*` for unordered, `1.` for ordered) consistently.
    *   Use standard emphasis (`**bold**`, `*italic*`).
    *   Format code blocks using triple backticks (```) with optional language identifiers (e.g., ```python).
    *   Use inline code with single backticks (`code`).
    *   Ensure proper spacing around lists and blocks for readability.
    *   Avoid complex or non-standard Markdown extensions unless absolutely necessary.
5.  Ensure the content helps users achieve the outcomes demonstrated in the video for this part of the flow.
6.  Output ONLY the raw, valid Markdown content for this file. Do not include any introductory text, explanations, apologies, or concluding remarks outside the Markdown itself.
{f'**Language:** Write the entire documentation section ONLY in {language}. Translate any headings or comments from the skeleton as needed, maintaining valid Markdown structure.' if language and language.lower() != "english" else ''}

**Input Data:**

### User Journey Flow (Overall Context):
{user_journey_flow}

### Transcript (Overall Context):
{transcript}

### Markdown Skeleton (for this specific file):
```markdown
{skeleton}
```

---
**Populated Markdown Content (for this file only):**
"""
                response = openai.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=1200 # Increased tokens for potentially longer content
                )
                # Ensure writing in UTF-8 for broader language support
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(response.choices[0].message.content)
            else:
                recurse(child, full_path)
    recurse(folder_structure, base_path)

# (Legacy) Single-step doc generator for reference

def generate_markdown(transcript, user_journey_flow, model="gpt-4o-mini"): # Added model parameter consistency
    system_prompt = "You are a technical writer creating a comprehensive how-to guide."
    user_prompt = f"""
Based on the provided Transcript and User Journey Flow from a product demo, create a clear, outcome-oriented, step-by-step guide in Markdown format.

**Goal:** Produce documentation that is easy to follow for someone wanting to achieve the same outcomes shown in the demo.

**Instructions:**
1.  Structure the guide logically, likely following the steps outlined in the User Journey Flow.
2.  For each significant step or section:
    *   Explain the user's goal for that step.
    *   Describe the practical application or use case.
    *   Provide clear, step-by-step instructions.
    *   Mention the benefits or outcomes of completing the step.
3.  Reference relevant details from the Transcript and context from the User Journey Flow.
4.  **Markdown Formatting:**
    *   Adhere strictly to **CommonMark** Markdown syntax.
    *   Use standard headings (`#`, `##`, `###`, etc.), ensuring correct hierarchy.
    *   Use standard lists (`-` or `*` for unordered, `1.` for ordered) consistently.
    *   Use standard emphasis (`**bold**`, `*italic*`).
    *   Format code blocks using triple backticks (```) with optional language identifiers (e.g., ```python).
    *   Use inline code with single backticks (`code`).
    *   Ensure proper spacing around lists and blocks for readability.
    *   Avoid complex or non-standard Markdown extensions.
5.  Output ONLY the raw, valid Markdown content for the complete guide. Do not include any introductory text, explanations, apologies, or concluding remarks outside the Markdown itself.

**Input Data:**

### User Journey Flow:
{user_journey_flow}

### Transcript:
{transcript}

---
**Generated How-To Guide (Markdown):**
"""
    response = openai.chat.completions.create(
        model=model, # Use specified model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=2000 # Allow for a longer single document
    )
    return response.choices[0].message.content
