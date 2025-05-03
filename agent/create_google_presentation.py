from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
from typing import List, Dict
import os
import uuid
from googleapiclient.http import MediaFileUpload


def create_google_feature_presentation(keyframe_summaries: List[str],
                                     user_journey: str,
                                     image_paths: List[str],
                                     output_path: str = "Application Features Overview") -> str:
    """
    Creates a professional Google Slides presentation highlighting the main features
    Returns the presentation ID
    """
    SCOPES = ['https://www.googleapis.com/auth/presentations', 
              'https://www.googleapis.com/auth/drive',
              'https://www.googleapis.com/auth/drive.file']
    SERVICE_ACCOUNT_FILE = '.\\the-better-hack-7337ffd8502d.json'

    # Define theme colors (converting from 0-255 to 0.0-1.0 range)
    THEME_COLOR_PRIMARY = {
        'red': 0.0,
        'green': 112/255,
        'blue': 192/255
    }     # Blue
    THEME_COLOR_SECONDARY = {
        'red': 1.0,
        'green': 1.0,
        'blue': 1.0
    } # White
    THEME_COLOR_ACCENT = {
        'red': 240/255,
        'green': 240/255,
        'blue': 240/255
    }    # Light gray

    # Authenticate and create the Slides and Drive services
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    slides_service = build('slides', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Create a new presentation
    presentation = slides_service.presentations().create(
        body={'title': output_path}
    ).execute()
    presentation_id = '1yUDrrmE_9fw3MGfjnMChnra-Z6qvncM5c9w257DvWfg'

    # Extract features
    features = _extract_main_features(user_journey)

    # Upload images to Drive and get their URLs
    image_urls = []
    for image_path in image_paths:
        if os.path.exists(image_path):
            file_metadata = {
                'name': os.path.basename(image_path),
                'mimeType': 'image/jpeg'
            }
            media = MediaFileUpload(image_path, mimetype='image/jpeg', resumable=True)
            file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            # Make the file publicly accessible
            drive_service.permissions().create(
                fileId=file.get('id'),
                body={'type': 'anyone', 'role': 'reader'},
                fields='id'
            ).execute()
            
            # Get the web content link
            image_url = f"https://drive.google.com/uc?id={file.get('id')}"
            image_urls.append(image_url)
        else:
            image_urls.append(None)

    # Prepare requests for batch update

    # Create title slide with unique ID
    title_slide_id = f'slide_{uuid.uuid4().hex[:8]}'  # Using UUID for unique ID
    slide_request = [{
        'createSlide': {
            'objectId': title_slide_id,
            'insertionIndex': '0',
            'slideLayoutReference': {
                'predefinedLayout': 'TITLE'
            }
        }
    }]

    # First create the slide
    body = {'requests': slide_request}
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id, body=body).execute()

    # Get the slide details to find the title placeholder ID
    slide = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()

    # Find the title placeholder ID from the first slide
    first_slide = slide.get('slides')[0]
    title_id = None
    for element in first_slide.get('pageElements', []):
        if element.get('shape', {}).get('placeholder', {}).get('type') == 'TITLE':
            title_id = f"{element.get('objectId')}_{uuid.uuid4().hex[:8]}"
            break

    if title_id:
        # Update subtitle and background shape IDs to be unique
        subtitle_id = f'subtitle_{title_slide_id}'
        background_id = f'background_{title_slide_id}'
        
        # Update title slide styling
        text_request = [{
            'insertText': {
                'objectId': title_id,
                'insertionIndex': 0,
                'text': output_path
            }
        },
        {
            'updateTextStyle': {
                'objectId': title_id,
                'style': {
                    'fontSize': {'magnitude': 44, 'unit': 'PT'},
                    'foregroundColor': {'opaqueColor': {'rgbColor': THEME_COLOR_PRIMARY}},
                    'bold': True
                },
                'fields': 'fontSize,foregroundColor,bold'
            }
        }]

        # Update subtitle request with unique ID
        subtitle_request = [{
            'createShape': {
                'objectId': subtitle_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': title_slide_id,
                    'size': {
                        'width': {'magnitude': 400, 'unit': 'PT'},
                        'height': {'magnitude': 50, 'unit': 'PT'}
                    },
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': 50,
                        'translateY': 100,
                        'unit': 'PT'
                    }
                }
            }
        },
        {
            'insertText': {
                'objectId': subtitle_id,
                'text': "Generated from User Journey Analysis"
            }
        },
        {
            'updateTextStyle': {
                'objectId': subtitle_id,
                'style': {
                    'fontSize': {'magnitude': 24, 'unit': 'PT'},
                    'italic': True
                },
                'fields': 'fontSize,italic'
            }
        }]

        # Update background request with unique ID
        background_request = [{
            'createShape': {
                'objectId': background_id,
                'shapeType': 'RECTANGLE',
                'elementProperties': {
                    'pageObjectId': title_slide_id,
                    'size': {
                        'width': {'magnitude': 720, 'unit': 'PT'},
                        'height': {'magnitude': 117, 'unit': 'PT'}
                    },
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': 0,
                        'translateY': 288,
                        'unit': 'PT'
                    }
                }
            }
        },
        {
            'updateShapeProperties': {
                'objectId': background_id,
                'shapeProperties': {
                    'shapeBackgroundFill': {
                        'solidFill': {
                            'color': {'rgbColor': THEME_COLOR_PRIMARY}
                        }
                    },
                    'outline': {'propertyState': 'NOT_RENDERED'}
                },
                'fields': 'shapeBackgroundFill.solidFill.color,outline'
            }
        }]

        # Combine all requests for title slide
        body = {'requests': text_request + subtitle_request + background_request}
        slides_service.presentations().batchUpdate(
            presentationId=presentation_id, body=body).execute()

    # Create feature slides
    requests = []
    for i, (feature, image_url) in enumerate(zip(features[:5], image_urls[:5])):
        slide_id = f'featureSlide_{i}_{uuid.uuid4().hex[:8]}'
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
                            'scaleY': 1.1,
                            'translateX': 120,
                            'translateY': 40,
                            'unit': 'PT'
                        }
                    }
                }
            },
            {
                'updateShapeProperties': {
                    'objectId': f'title_{i}',
                    'shapeProperties': {
                        'shapeBackgroundFill': {
                            'solidFill': {
                                'color': {'rgbColor': THEME_COLOR_ACCENT}
                            }
                        }
                    },
                    'fields': 'shapeBackgroundFill.solidFill.color'
                }
            },
            {
                'insertText': {
                    'objectId': f'title_{i}',
                    'text': feature['title']
                }
            }
        ])

        # Create feature number circle
        feature_number_requests = [{
            'createShape': {
                'objectId': f'featureNum_{i}',
                'shapeType': 'ELLIPSE',
                'elementProperties': {
                    'pageObjectId': slide_id,
                    'size': {
                        'width': {'magnitude': 72, 'unit': 'PT'},
                        'height': {'magnitude': 72, 'unit': 'PT'}
                    },
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': 36,
                        'translateY': 36,
                        'unit': 'PT'
                    }
                }
            }
        },
        {
            'updateShapeProperties': {
                'objectId': f'featureNum_{i}',
                'shapeProperties': {
                    'shapeBackgroundFill': {
                        'solidFill': {
                            'color': {'rgbColor': THEME_COLOR_PRIMARY}
                        }
                    },
                    'outline': {'propertyState': 'NOT_RENDERED'}
                },
                'fields': 'shapeBackgroundFill.solidFill.color,outline'
            }
        },
        {
            'insertText': {
                'objectId': f'featureNum_{i}',
                'text': str(i + 1)
            }
        },
        {
            'updateTextStyle': {
                'objectId': f'featureNum_{i}',
                'style': {
                    'fontSize': {'magnitude': 24, 'unit': 'PT'},
                    'foregroundColor': {'opaqueColor': {'rgbColor': THEME_COLOR_SECONDARY}},
                    'bold': True
                },
                'fields': 'fontSize,foregroundColor,bold'
            }
        }]

        # Update existing title styling
        title_requests = [{
            'updateTextStyle': {
                'objectId': f'title_{i}',
                'style': {
                    'fontSize': {'magnitude': 32, 'unit': 'PT'},
                    'foregroundColor': {'opaqueColor': {'rgbColor': THEME_COLOR_PRIMARY}},
                    'bold': True
                },
                'fields': 'fontSize,foregroundColor,bold'
            }
        }]

        # Add description text box
        description_requests = [{
            'createShape': {
                'objectId': f'description_{i}',
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': slide_id,
                    'size': {
                        'width': {'magnitude': 252, 'unit': 'PT'},
                        'height': {'magnitude': 216, 'unit': 'PT'}
                    },
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': 396,
                        'translateY': 130,
                        'unit': 'PT'
                    }
                }
            }
        },
        {
            'insertText': {
                'objectId': f'description_{i}',
                'text': feature['description']
            }
        },
        {
            'updateTextStyle': {
                'objectId': f'description_{i}',
                'style': {
                    'fontSize': {'magnitude': 16, 'unit': 'PT'}
                },
                'fields': 'fontSize'
            }
        }]

        requests.extend(feature_number_requests + title_requests + description_requests)

        # Add image if it exists and we have a valid URL
        if image_url:
            image_requests = [{
                'createImage': {
                    'objectId': f'image_{i}',
                    'url': image_url,
                    'elementProperties': {
                        'pageObjectId': slide_id,
                        'size': {
                            'width': {'magnitude': 288, 'unit': 'PT'},  # 4 inches
                            'height': {'magnitude': 162, 'unit': 'PT'}  # 2.25 inches (16:9 aspect ratio)
                        },
                        'transform': {
                            'scaleX': 1,
                            'scaleY': 1,
                            'translateX': 72,  # 1 inch from left
                            'translateY': 140,  # 3 inches from top
                            'unit': 'PT'
                        }
                    }
                }
            }]
            requests.extend(image_requests)

    # Execute the requests
    body = {'requests': requests}
    slides_service.presentations().batchUpdate(
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
    
    # Ensure we have a list of features
    if isinstance(features, dict) and 'features' in features:
        return features['features']
    elif isinstance(features, list):
        return features
    else:
        # If the response is not in the expected format, create a default structure
        return [{'title': 'Feature', 'description': 'Description'} for _ in range(5)]