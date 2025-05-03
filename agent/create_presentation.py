from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import os
import json
from typing import List, Dict

def create_feature_presentation(keyframe_summaries: List[str], 
                              user_journey: str,
                              image_paths: List[str],
                              output_path: str = "output/presentation"):
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
    
    # Format title slide
    title.text = "Application Features Overview"
    title.text_frame.paragraphs[0].font.size = Pt(44)
    title.text_frame.paragraphs[0].font.bold = True
    title.text_frame.paragraphs[0].font.color.rgb = theme_color_primary
    
    subtitle.text = "Generated from User Journey Analysis"
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
    features = _extract_main_features(user_journey)
    
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
    summary_para.text = "Key Features Summary"
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