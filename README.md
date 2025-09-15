# AI-Powered Excel Mock Interviewer

An intelligent, conversational AI agent that conducts mock technical interviews to assess a candidate's proficiency in Microsoft Excel. [cite_start]This project is designed to automate the initial screening process, providing consistent evaluations and detailed feedback[cite: 7, 12, 18].

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR_APP_URL_HERE) ## 🌟 Core Features

- [cite_start]**Conversational AI Agent**: The interviewer, "Alex," guides the candidate through a structured interview flow, from introduction to conclusion[cite: 16, 17].
- **Dynamic Question Engine**: Randomly selects a mix of easy, medium, and hard questions from a predefined JSON file for each interview session.
- **Intelligent Answer Evaluation**: Uses Google's Gemini LLM to analyze the candidate's answers, assigning a score (1-5) and providing constructive, conversational feedback.
- **Real-time Video Proctoring**: Utilizes the candidate's webcam and a Hugging Face object detection model to monitor for potential malpractice, such as multiple people in the room or cell phone usage.
- **Automated Session Termination**: The interview is automatically terminated if the candidate turns off their camera or accumulates 3 proctoring warnings.
- **Comprehensive Performance Dashboard**: After the interview, a detailed report is generated, showing an overall summary, a question-by-question breakdown of scores, and the feedback received.
- **User Authentication & Persistence**: A secure login system for candidates, with all interview results saved to a SQLite database for review.

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Generative AI**: Google Gemini 1.5 Flash
- **Video Proctoring**: Streamlit-WebRTC, PyTorch, Hugging Face Transformers (`facebook/detr-resnet-50`)
- **Database**: SQLite
- **Core Libraries**: Pandas

## 📂 Project Structure

excel-interviewer/
├── .streamlit/
│ └── secrets.toml
├── components/
│ ├── interview_card.py
│ └── proctoring.py
├── app.py
├── candidates.db
├── database.py
├── prompts.py
├── questions.json
└── requirements.txt

## 🚀 Local Setup and Installation

1.  **Clone the Repository**

    ```bash
    git clone [https://github.com/code-to-horizon/Excel_AI_Interviewer.git](https://github.com/code-to-horizon/Excel_AI_Interviewer.git)
    cd YOUR_REPOSITORY_NAME
    ```

2.  **Create a Virtual Environment** (Recommended)

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up API Key**

    - Create a file: `.streamlit/secrets.toml`.
    - Add your Google API key to it:
      ```toml
      GOOGLE_API_KEY = "YOUR_API_KEY_HERE"
      ```

5.  **Run the Application**
    The application database `candidates.db` is pre-populated with sample users.
    ```bash
    streamlit run app.py
    ```

## 📋 Usage

- Open the application in your browser (usually `http://localhost:8501`).
- Log in with one of the sample credentials:
  - UserID: `priya_s`, Password: `pass123`
  - UserID: `amit_k`, Password: `pass456`
  - UserID: `sneha_p`, Password: `pass789`
- Click "Start Interview" and grant camera permissions to begin.

## ⚙️ Configuration

The `MOCK_API_CALLS` flag in `app.py` can be set to `True` to run the application without making actual calls to the Gemini API, using placeholder responses instead. This is useful for UI development and testing.

````python
# In app.py
MOCK_API_CALLS = True

---

### 2. `requirements.txt` (Project Dependencies)

This file lists all the Python packages required for your project. The `streamlit-modal` package was in your original file but wasn't used, so it has been removed for a cleaner deployment.

```text
streamlit
google-generativeai
pandas
streamlit-webrtc
torch
transformers
Pillow
timm
````
