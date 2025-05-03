from googleapiclient.discovery import build
from google.oauth2 import service_account
import json
from typing import List, Dict
import os
import uuid
from googleapiclient.http import MediaFileUpload
import pickle
from pathlib import Path

# Define cache directory for presentation metadata
PRESENTATION_CACHE_DIR = Path("cache/presentations")
PRESENTATION_CACHE_DIR.mkdir(exist_ok=True)

def get_presentation_cache_path(presentation_id: str) -> Path:
    """Get the cache path for a presentation's metadata"""
    return PRESENTATION_CACHE_DIR / f"{presentation_id}.pkl"

def store_presentation_metadata(presentation_id: str, features: List[Dict], image_paths: List[str]):
    """Store presentation metadata for future comparison"""
    metadata = {
        'features': features,
        'image_paths': image_paths,
        'timestamp': os.path.getmtime(image_paths[0]) if image_paths else None
    }
    
    cache_path = get_presentation_cache_path(presentation_id)
    with open(cache_path, 'wb') as f:
        pickle.dump(metadata, f)

def load_presentation_metadata(presentation_id: str) -> Dict:
    """Load stored presentation metadata"""
    cache_path = get_presentation_cache_path(presentation_id)
    if cache_path.exists():
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    return None

def compare_presentations(old_metadata: Dict, new_features: List[Dict], new_image_paths: List[str]) -> Dict:
    """Compare old and new presentation content and return differences"""
    if not old_metadata:
        return {
            'is_new': True,
            'changes': None
        }
    
    changes = {
        'features': [],
        'images': []
    }
    
    # Compare features
    old_features = old_metadata['features']
    for i, (old_feature, new_feature) in enumerate(zip(old_features, new_features)):
        if old_feature['title'] != new_feature['title'] or old_feature['description'] != new_feature['description']:
            changes['features'].append({
                'index': i,
                'old': old_feature,
                'new': new_feature
            })
    
    # Compare images
    old_image_paths = old_metadata['image_paths']
    for i, (old_path, new_path) in enumerate(zip(old_image_paths, new_image_paths)):
        if old_path != new_path:
            changes['images'].append({
                'index': i,
                'old_path': old_path,
                'new_path': new_path
            })
    
    return {
        'is_new': False,
        'changes': changes if any(changes['features']) or any(changes['images']) else None
    }

def get_slide_id(slides_service, presentation_id: str, slide_index: int) -> str:
    """Get the ID of an existing slide by its index"""
    presentation = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()
    
    slides = presentation.get('slides', [])
    if 0 <= slide_index < len(slides):
        return slides[slide_index].get('objectId')
    return None

def add_change_comment(slides_service, presentation_id: str, slide_id: str, change_text: str):
    """Add a comment box to a slide showing changes"""
    if not slide_id:
        print(f"Warning: Could not find slide to add comment")
        return
        
    comment_id = f'comment_{uuid.uuid4().hex[:8]}'
    comment_request = [{
        'createShape': {
            'objectId': comment_id,
            'shapeType': 'TEXT_BOX',
            'elementProperties': {
                'pageObjectId': slide_id,
                'size': {
                    'width': {'magnitude': 400, 'unit': 'PT'},
                    'height': {'magnitude': 100, 'unit': 'PT'}
                },
                'transform': {
                    'scaleX': 1,
                    'scaleY': 1,
                    'translateX': 50,
                    'translateY': 50,
                    'unit': 'PT'
                }
            }
        }
    },
    {
        'updateShapeProperties': {
            'objectId': comment_id,
            'shapeProperties': {
                'shapeBackgroundFill': {
                    'solidFill': {
                        'color': {'rgbColor': {'red': 1.0, 'green': 0.9, 'blue': 0.8}}  # Light orange
                    }
                },
                'outline': {
                    'dashStyle': 'DASH',
                    'weight': {'magnitude': 1, 'unit': 'PT'},
                    'outlineFill': {
                        'solidFill': {
                            'color': {'rgbColor': {'red': 1.0, 'green': 0.5, 'blue': 0.0}}  # Orange
                        }
                    }
                }
            },
            'fields': 'shapeBackgroundFill.solidFill.color,outline'
        }
    },
    {
        'insertText': {
            'objectId': comment_id,
            'text': f"Changes detected:\n{change_text}"
        }
    },
    {
        'updateTextStyle': {
            'objectId': comment_id,
            'style': {
                'fontSize': {'magnitude': 12, 'unit': 'PT'},
                'foregroundColor': {'opaqueColor': {'rgbColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2}}},  # Dark gray
                'bold': True
            },
            'fields': 'fontSize,foregroundColor,bold'
        }
    }]
    
    body = {'requests': comment_request}
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id, body=body).execute()

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

    # Check for changes from previous version
    old_metadata = load_presentation_metadata(presentation_id)
    changes = compare_presentations(old_metadata, features, image_paths)
    
    if changes['is_new']:
        # First time run - create the presentation normally
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
    else:
        # Subsequent runs - only add changelog comments
        if changes['changes']:
            print("\nChanges detected in presentation:")
            if changes['changes']['features']:
                print("\nFeature changes:")
                for change in changes['changes']['features']:
                    print(f"\nSlide {change['index'] + 1}:")
                    print(f"Old title: {change['old']['title']}")
                    print(f"New title: {change['new']['title']}")
                    print(f"Old description: {change['old']['description']}")
                    print(f"New description: {change['new']['description']}")
                    
                    # Get the existing slide ID
                    slide_id = get_slide_id(slides_service, presentation_id, change['index'] + 1)  # +1 for title slide
                    if slide_id:
                        change_text = f"Title would change from:\n'{change['old']['title']}'\nto:\n'{change['new']['title']}'\n\nDescription would change from:\n'{change['old']['description']}'\nto:\n'{change['new']['description']}'"
                        add_change_comment(slides_service, presentation_id, slide_id, change_text)
            
            if changes['changes']['images']:
                print("\nImage changes:")
                for change in changes['changes']['images']:
                    print(f"\nSlide {change['index'] + 1}:")
                    print(f"Old image: {change['old_path']}")
                    print(f"New image: {change['new_path']}")
                    
                    # Get the existing slide ID
                    slide_id = get_slide_id(slides_service, presentation_id, change['index'] + 1)  # +1 for title slide
                    if slide_id:
                        change_text = f"Image would change from:\n'{change['old_path']}'\nto:\n'{change['new_path']}'"
                        add_change_comment(slides_service, presentation_id, slide_id, change_text)
        else:
            print("\nNo changes detected in presentation content.")

    # Store current metadata
    store_presentation_metadata(presentation_id, features, image_paths)

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