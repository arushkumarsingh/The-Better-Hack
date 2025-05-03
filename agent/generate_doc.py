import openai

openai.api_key = "your_openai_key"

def generate_markdown(transcript, keyframe_descriptions):
    prompt = f"""
You are a technical writer. Based on the transcript below and key visuals, create clear step-by-step software documentation in markdown.

Transcript:
{transcript}

Screenshots:
{keyframe_descriptions}

Use headings, bullet points, and numbered steps.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
