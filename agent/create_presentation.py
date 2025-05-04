from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import os
import json
from typing import List, Dict
from agent.create_google_presentation import create_google_feature_presentation

def create_feature_presentation(keyframe_summaries: List[str], 
                              user_journey: str,
                              image_paths: List[str],
                              output_path: str = "output/presentation",
                              language: str = None):
    """
    Creates a professional PowerPoint presentation highlighting the main features
    with proper text wrapping and formatting
    """
    prs = Presentation()
    
    # Define slide dimensions
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)  # 16:9 aspect ratio
    
    # Set theme colors
    theme_color_primary = RGBColor(0, 112, 192)     # Blue
    theme_color_secondary = RGBColor(255, 255, 255) # White
    theme_color_accent = RGBColor(240, 240, 240)    # Light gray
    
    # Title slide
    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = title_slide.shapes.title
    subtitle = title_slide.placeholders[1]

    # Localize static text if language is specified and not English
    localized_title = "Application Features Overview"
    localized_subtitle = "Generated from User Journey Analysis"
    localized_summary = "Key Features Summary"
    if language and language.lower() != "english":
        import openai
        system_prompt = "You are an expert translator specializing in UI text."
        user_prompt = f"""
Translate the following English phrases into {language}.

**Input Phrases:**
- title: Application Features Overview
- subtitle: Generated from User Journey Analysis
- summary: Key Features Summary

**Output Format:**
Return ONLY a valid JSON object with the translated phrases assigned to the corresponding keys ('title', 'subtitle', 'summary').

Example for Spanish:
```json
{{
  "title": "Resumen de las Características de la Aplicación",
  "subtitle": "Generado a partir del Análisis del Recorrido del Usuario",
  "summary": "Resumen de Características Clave"
}}
```

**Translate to:** {language}

**Output (JSON only):**
"""
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200 # Slightly increased for safety
        )
        import json
        try:
            translations = json.loads(response.choices[0].message.content.strip())
            localized_title = translations.get('title', localized_title)
            localized_subtitle = translations.get('subtitle', localized_subtitle)
            localized_summary = translations.get('summary', localized_summary)
        except Exception:
            pass
    # Format title slide
    title.text = localized_title
    title.text_frame.paragraphs[0].font.size = Pt(44)
    title.text_frame.paragraphs[0].font.bold = True
    title.text_frame.paragraphs[0].font.color.rgb = theme_color_primary

    subtitle.text = localized_subtitle
    subtitle.text_frame.paragraphs[0].font.size = Pt(24)
    subtitle.text_frame.paragraphs[0].font.italic = True
    
    # Add background shape to title slide
    background = title_slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, Inches(4), prs.slide_width, Inches(1.625)
    )
    background.fill.solid()
    background.fill.fore_color.rgb = theme_color_primary
    background.line.fill.background()  # No outline
    
    # Extract main features from user journey
    features = _extract_main_features(user_journey, language=language)
    
    # Create feature slides
    for i, (feature, image_path) in enumerate(zip(features[:5], image_paths[:5])):
        feature_slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
        
        # Add feature number for visual interest
        feature_num = feature_slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(0.5), Inches(0.5), Inches(1), Inches(1)
        )
        feature_num.fill.solid()
        feature_num.fill.fore_color.rgb = theme_color_primary
        feature_num.line.fill.background()  # No outline
        
        # Add number text to the oval
        num_textframe = feature_num.text_frame
        num_textframe.text = str(i+1)
        num_textframe.paragraphs[0].alignment = PP_ALIGN.CENTER
        num_textframe.paragraphs[0].font.size = Pt(24)
        num_textframe.paragraphs[0].font.bold = True
        num_textframe.paragraphs[0].font.color.rgb = theme_color_secondary
        num_textframe.vertical_anchor = MSO_ANCHOR.MIDDLE
        
        # Add title with colored background
        title_shape = feature_slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(1.7), Inches(0.5), Inches(7.8), Inches(1)
        )
        title_shape.fill.solid()
        title_shape.fill.fore_color.rgb = theme_color_accent
        title_shape.line.fill.background()  # No outline
        
        # Add title text
        title_textbox = feature_slide.shapes.add_textbox(
            Inches(1.8), Inches(0.65), Inches(7.5), Inches(0.7)
        )
        title_textframe = title_textbox.text_frame
        title_para = title_textframe.add_paragraph()
        title_para.text = feature['title']
        title_para.font.size = Pt(32)
        title_para.font.bold = True
        title_para.font.color.rgb = theme_color_primary
        
        # Add image
        if os.path.exists(image_path):
            left = Inches(1)
            top = Inches(1.8)
            pic = feature_slide.shapes.add_picture(
                image_path, 
                left, 
                top, 
                width=Inches(4)
            )
        
        # Add description with proper text wrapping
        textbox = feature_slide.shapes.add_textbox(
            left=Inches(5.5), 
            top=Inches(1.8),
            width=Inches(3.5),
            height=Inches(3)
        )
        text_frame = textbox.text_frame
        text_frame.word_wrap = True
        
        # Add description paragraph with proper formatting
        p = text_frame.add_paragraph()
        p.text = feature['description']
        p.font.size = Pt(16)
        p.alignment = PP_ALIGN.LEFT
        text_frame.auto_size = True  # Auto-size text to fit in textbox
        
    # Create summary slide
    summary_slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
    
    # Add title
    summary_title = summary_slide.shapes.add_textbox(
        Inches(1), Inches(0.5), Inches(8), Inches(1)
    )
    summary_title_frame = summary_title.text_frame
    summary_para = summary_title_frame.add_paragraph()
    summary_para.text = localized_summary
    summary_para.font.size = Pt(40)
    summary_para.font.bold = True
    summary_para.font.color.rgb = theme_color_primary
    
    # Add summary list
    summary_textbox = summary_slide.shapes.add_textbox(
        Inches(1), Inches(1.7), Inches(8), Inches(3)
    )
    summary_frame = summary_textbox.text_frame
    summary_frame.word_wrap = True
    
    # Add each feature as a bullet point
    for i, feature in enumerate(features[:5]):
        bullet_para = summary_frame.add_paragraph()
        bullet_para.text = f"{feature['title']}: {feature['description'].split('.')[0]}."
        bullet_para.font.size = Pt(18)
        bullet_para.level = 0  # First level bullet
        bullet_para.space_after = Pt(12)  # Space between bullets
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Save presentation
    output_file = f"{output_path}/feature_overview.pptx"
    prs.save(output_file)
    return output_file

def _extract_main_features(user_journey: str, language: str = None) -> List[Dict]:
    """
    Extracts main features from user journey text
    Returns list of dicts with 'title' and 'description'
    """
    # Use OpenAI to extract main features
    import openai

    system_prompt = "You are a feature analyst expert at summarizing key application capabilities from user journey descriptions."
    user_prompt = f"""
Analyze the provided User Journey description and identify the top 5 main features or capabilities demonstrated.

**Instructions:**
1.  Identify the 5 most prominent and distinct features shown in the journey.
2.  For each feature, provide:
    *   `title`: A concise title (2-4 words).
    *   `description`: A brief description (1-3 sentences) explaining the feature's purpose or benefit.
{f'3.  Generate the titles and descriptions ONLY in {language}.' if language and language.lower() != "english" else ''}

**Output Format:**
Return ONLY a valid JSON object containing a single key "features" whose value is a list of the 5 feature objects. Example:
```json
{{
  "features": [
    {{
      "title": "Feature Title 1",
      "description": "Description of feature 1."
    }},
    {{
      "title": "Feature Title 2",
      "description": "Description of feature 2."
    }},
    ... (up to 5 features)
  ]
}}
```

**Input Data:**

### User Journey:
{user_journey}

---
**Top 5 Features (JSON object only):**
"""

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={ "type": "json_object" },
        max_tokens=500 # Adjusted max_tokens
    )

    # Parse the JSON string into a Python dictionary
    try:
        content = json.loads(response.choices[0].message.content)
        # Validate structure slightly
        if isinstance(content, dict) and 'features' in content and isinstance(content['features'], list):
             return content['features']
        else:
             print("[WARN] Unexpected JSON structure received from feature extraction.")
             # Attempt to return the raw list if possible, or empty list
             return content.get('features', []) if isinstance(content, dict) else []
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to decode JSON from feature extraction: {e}")
        print("Raw response:", response.choices[0].message.content)
        return [] # Return empty list on error
