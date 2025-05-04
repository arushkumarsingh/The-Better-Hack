# Adaptidemo: The Better Hack

Adaptidemo is a full-stack application designed to automate the creation of user guides and customer-facing collateral from UI videos or screenshots. It leverages advanced screen recording, video processing, and AI-powered documentation generation to streamline product documentation and demo creation.

## 🚀 Features

- **Screen Recording:** Record your screen (with audio and camera overlay) directly from the web UI. 
- **Video & Image Upload:** Upload UI walkthrough videos or screenshots for documentation generation.
- **Automated Documentation:** Generate detailed, step-by-step markdown guides from your uploads.
- **Customer Deck Generation:** Automatically create feature presentations and customer decks from video content.
- **Persona-based Output:** Personalize documentation for different roles (e.g., Product Manager, Marketer, Developer).
- **Multi-language Support:** Generate documentation in multiple languages.
- **Downloadable Outputs:** Download generated guides and presentations in various formats.

## 🛠️ Setup Instructions

### Backend (Python FastAPI)

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd The-Better-Hack
   ```
2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Run the backend API:**
   ```bash
   uvicorn api:app --reload
   ```

### Frontend (React + TypeScript)

1. **Navigate to the frontend directory:**
   ```bash
   cd feature-scribe-studio
   ```
2. **Install dependencies:**
   ```bash
   npm install
   ```
3. **Run the frontend app:**
   ```bash
   npm start
   ```

4. **Access the app:**
   Open your browser and go to [http://localhost:3000](http://localhost:3000)

## 📝 Usage
- Click **Screen Record** to capture a new UI walkthrough, or upload an existing video/image.
- Select your target output (User Guide or Customer Deck) and persona.
- Wait for the AI to process your upload and generate documentation.
- Download the generated collateral or presentation.

## 👥 Contributors
- Arush Kumar Singh
- Shruti Sagar
- Mohd Hussam
- Siddharth Jha

> _Replace the placeholder names above with the actual contributor names._

---

For any issues, suggestions, or contributions, please open an issue or pull request!