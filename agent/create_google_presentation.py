from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
from typing import List, Dict
import os

def create_google_feature_presentation(keyframe_summaries: List[str],
                                     user_journey: str,
                                     image_paths: List[str],
                                     output_path: str = "Application Features Overview") -> str:
    """
    Creates a professional Google Slides presentation highlighting the main features
    Returns the presentation ID
    """
    SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = '.\\the-better-hack-7337ffd8502d.json'  # Update this path

    # Authenticate and create the Slides service
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('slides', 'v1', credentials=creds)

    # Create a new presentation
    presentation = service.presentations().create(
        body={'title': output_path}
    ).execute()
    presentation_id = '1yUDrrmE_9fw3MGfjnMChnra-Z6qvncM5c9w257DvWfg'

    # Extract features
    features = _extract_main_features(user_journey)

    # Prepare requests for batch update

    # Create title slide
    slide_request = [{
        'createSlide': {
            'objectId': 'titleSlide',
            'insertionIndex': '0',
            'slideLayoutReference': {
                'predefinedLayout': 'TITLE'
            }
        }
    }]

    # First create the slide
    body = {'requests': slide_request}
    service.presentations().batchUpdate(
        presentationId=presentation_id, body=body).execute()

    # Get the slide details to find the title placeholder ID
    slide = service.presentations().get(
        presentationId=presentation_id
    ).execute()

    # Find the title placeholder ID from the first slide
    first_slide = slide.get('slides')[0]
    title_id = None
    for element in first_slide.get('pageElements', []):
        if element.get('shape', {}).get('placeholder', {}).get('type') == 'TITLE':
            title_id = element.get('objectId')
            break

    if title_id:
        # Now insert the text into the title placeholder
        text_request = [{
            'insertText': {
                'objectId': title_id,
                'insertionIndex': 0,
                'text': output_path
            }
        }]
        body = {'requests': text_request}
        service.presentations().batchUpdate(
            presentationId=presentation_id, body=body).execute()

    # Create feature slides
    requests = []
    for i, (feature, image_path) in enumerate(zip(features[:5], image_paths[:5])):
        slide_id = f'featureSlide_{i}'
        requests.extend([
            {
                'createSlide': {
                    'objectId': slide_id,
                    'insertionIndex': str(i + 1),
                    'slideLayoutReference': {
                        'predefinedLayout': 'BLANK'
                    }
                }
            },
            {
                'createShape': {
                    'objectId': f'title_{i}',
                    'shapeType': 'TEXT_BOX',
                    'elementProperties': {
                        'pageObjectId': slide_id,
                        'size': {
                            'width': {'magnitude': 600, 'unit': 'PT'},
                            'height': {'magnitude': 50, 'unit': 'PT'}
                        },
                        'transform': {
                            'scaleX': 1,
                            'scaleY': 1,
                            'translateX': 50,
                            'translateY': 30,
                            'unit': 'PT'
                        }
                    }
                }
            },
            {
                'insertText': {
                    'objectId': f'title_{i}',
                    'text': feature['title']
                }
            }
            # Add more requests for description and formatting
        ])

        # If image exists, create request to upload it
        if os.path.exists(image_path):
            # Upload image and create image request
            # Note: Image upload requires different approach with Google Slides API
            pass

    # Execute the requests
    body = {'requests': requests}
    service.presentations().batchUpdate(
        presentationId=presentation_id, body=body).execute()

    return presentation_id

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