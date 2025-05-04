import openai
import os
import base64
from typing import List

# Summarize a single keyframe image using OpenAI Vision

from PIL import Image
import io

def summarize_keyframe(image_path: str, timestamp: str, openai_model: str = "gpt-4o-mini", previous_context: str = None) -> str:
    # Resize image to width=512px, maintain aspect ratio
    img = Image.open(image_path)
    w, h = img.size
    if w > 512:
        new_h = int(h * 512 / w)
        img = img.resize((512, new_h), Image.LANCZOS)
    # Save to JPEG in-memory
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    img_bytes = buf.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    image_url = f"data:image/jpeg;base64,{img_b64}"
    context_instruction = ""
    if previous_context:
        context_instruction = f"\n\n**Previous Context:**\n{previous_context}\nConnect this context to the current summary for narrative continuity."
    else:
        context_instruction = ""

    response = openai.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": "You are an expert at analyzing UI screenshots and describing user actions and application state."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze the application screenshot provided.

                        **Instructions:**
                        1.  Start your response *immediately* with the timestamp in [mm:ss] format: {timestamp}
                        2.  Describe the primary user action or application state visible.
                        3.  Mention key visible UI elements involved (buttons, menus, fields).
                        4.  Note any apparent transitions or changes from a previous state (if applicable, based on the context below).
                        5.  Be concise and focus only on what is visible.

                        **Timestamp:** {timestamp}
                        {context_instruction}"""
                    },
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        max_tokens=200 # Keep max_tokens or adjust if needed
    )
    summary = response.choices[0].message.content.strip()
    # The check 'if not summary.startswith(timestamp):' might become redundant
    # if the model consistently follows the new instruction 1. Can be kept for safety.
    # Ensure timestamp is present at the start (Safety check)
    if not summary.startswith(f"[{timestamp.split(':')[0]}:{timestamp.split(':')[1]}]"): # Check format [mm:ss]
         # Attempt to find timestamp pattern if not at start
         import re
         match = re.search(r"\[\d{1,2}:\d{2}\]", summary)
         if match:
             # If found elsewhere, move it to the start
             ts = match.group(0)
             summary = ts + " " + summary.replace(ts, "").strip()
         else:
             # If not found at all, prepend it
             summary = f"[{timestamp.split(':')[0]}:{timestamp.split(':')[1]}] {summary}"

    return summary

# Consolidate all keyframe summaries into a user journey flow

def consolidate_user_journey(summaries: List[str]) -> str:
    system_prompt = "You are an outcome-oriented product educator and UX analyst, skilled at creating clear, practical 'How-To' guides from application usage summaries."

    instruction_prompt = """
Based on the provided step-wise summaries from key application screenshots, create a clear, numbered 'How-To User Journey Guide'.

**Your Goal:** Produce a guide focused on user goals, practical benefits, and actionable steps to achieve outcomes shown in the demo. Avoid technical jargon and repetition.

**Requirements for the Guide:**
1.  **Overall Flow:** Start with a brief description of the overall workflow and the main practical outcomes the user can achieve.
2.  **Main Use Cases:** Briefly highlight the primary applications or use cases demonstrated.
3.  **Numbered Steps:** For each summary provided:
    *   **Explain the Goal:** What is the user trying to accomplish in this step? What is the real-world use case?
    *   **Identify Interactable Elements:** List visible clickable buttons, fields, or interactive elements. For each, estimate its likely function based on label, icon, or context.
    *   **Describe Action/Outcome:** Clearly state the action taken and the resulting state or benefit.
    *   **Use Outcome-Focused Language:** Emphasize what the user achieves.

**Output Format for Each Step:** Follow this structure precisely:

**Step [Number]: [Concise Step Goal/Action]**
*   **Use Case:** [Brief explanation of the real-world scenario]
*   **Visible Elements:**
    *   [Element Name/Description]: [Likely Function]
    *   ... (list all relevant elements)
*   **Guidance/Outcome:** [Description of the action taken and the result/benefit]

---
**Input Summaries:**
"""

    # Append numbered summaries to the instruction prompt
    input_data = "\n".join([f"{i}. {summary}" for i, summary in enumerate(summaries, 1)])

    full_user_prompt = instruction_prompt + "\n" + input_data + "\n\n---\n**How-To User Journey Guide:**"

    response = openai.chat.completions.create(
        model="gpt-4o", # Keep model or adjust
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user_prompt}
        ],
        max_tokens=1000 # Increased slightly to accommodate structure, adjust as needed
    )
    return response.choices[0].message.content
