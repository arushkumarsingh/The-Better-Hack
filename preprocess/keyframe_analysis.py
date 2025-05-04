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
        context_instruction = f"\nThe previous keyframe context is: {previous_context}\nConnect this context to the current summary for narrative continuity."
    response = openai.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": "You are an expert at analyzing UI screenshots and describing user actions and application state."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Describe what is happening in this application screenshot. Focus on user actions, visible UI elements, and any transitions or changes. The timestamp for this keyframe is {timestamp}. Include this timestamp at the start of your summary in the format [mm:ss].{context_instruction}"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        max_tokens=200
    )
    summary = response.choices[0].message.content.strip()
    # Ensure timestamp is present at the start
    if not summary.startswith(timestamp):
        summary = f"{timestamp} {summary}"
    return summary

# Consolidate all keyframe summaries into a user journey flow

def consolidate_user_journey(summaries: List[str]) -> str:
    prompt = """
You are an outcome-oriented product educator and UX analyst. Given the following step-wise summaries of key application screenshots, consolidate them into a clear, numbered 'How-To User Journey Guide' that describes:
- The overall flow and practical outcomes the user can achieve with the app.
- For each step, explain what the user is trying to accomplish, the real-world use case, and how it fits into the broader application or workflow.
- Highlight the main applications and use cases covered by the demo.
- For each step, list all clickable buttons or interactive elements visible on the screen, and provide your best estimate of what each button does (based on its label, icon, or context).
- Focus on user goals, practical benefits, and actionable guidance, not technical details.
- Present this information in a structured way for each step: include clickable elements, their likely function, and navigation mapping.
- Use clear, outcome-focused language and avoid repetition.

Summaries:
"""
    for i, summary in enumerate(summaries, 1):
        prompt += f"{i}. {summary}\n"
    prompt += "\nHow-To User Journey Guide (numbered steps, with a description of visible UI elements, use cases, user goals, and actionable outcomes of each step):"
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800
    )
    return response.choices[0].message.content
