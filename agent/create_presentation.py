from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
import os
import json
from typing import List, Dict

def create_feature_presentation(keyframe_summaries: List[str], 
                              user_journey: str,
                              image_paths: List[str],
                              output_path: str = "output/presentation"):
    """
    Creates a PowerPoint presentation highlighting the main features
    """
    prs = Presentation()
    
    # Title slide
    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = title_slide.shapes.title
    subtitle = title_slide.placeholders[1]
    title.text = "Application Features Overview"
    subtitle.text = "Generated from User Journey Analysis"

    # Extract main features from user journey
    features = _extract_main_features(user_journey)
    
    # Create feature slides
    for feature, image_path in zip(features[:5], image_paths[:5]):  # Limit to top 5 features
        feature_slide = prs.slides.add_slide(prs.slide_layouts[5])
        
        # Add title
        title = feature_slide.shapes.title
        title.text = feature['title']
        
        # Add image
        if os.path.exists(image_path):
            left = Inches(1)
            top = Inches(2)
            pic = feature_slide.shapes.add_picture(image_path, left, top, 
                                                 width=Inches(4))
        
        # Add description
        textbox = feature_slide.shapes.add_textbox(left=Inches(6), 
                                                 top=Inches(2),
                                                 width=Inches(3),
                                                 height=Inches(4))
        text_frame = textbox.text_frame
        p = text_frame.add_paragraph()
        p.text = feature['description']
        p.font.size = Pt(14)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Save presentation
    prs.save(f"{output_path}/feature_overview.pptx")
    return f"{output_path}/feature_overview.pptx"

def _extract_main_features(user_journey: str) -> List[Dict]:
    """
    Extracts main features from user journey text
    Returns list of dicts with 'title' and 'description'
    """
    # Use OpenAI to extract main features
    import openai
    
    prompt = """
    Given this user journey, identify the top 5 main features of the application.
    For each feature provide:
    1. A short title (2-4 words)
    2. A brief description (2-3 sentences)
    Format as JSON list of objects with 'title' and 'description' fields.
    
    User Journey:
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", 
             "content": prompt + user_journey}
        ],
        response_format={ "type": "json_object" }
    )
    
    # Parse the JSON string into a Python dictionary
    
    features = json.loads(response.choices[0].message.content)
    return features['features']