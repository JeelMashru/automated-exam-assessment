# API Configuration & Setup Guide

This guide explains how to acquire, configure, and verify API keys for the **Automated Descriptive Exam Assessment Engine**.

---

## 1. Google Gemini API Setup (Recommended)

ExamJudge AI uses the official **`google-genai` Python SDK** to communicate with Google's Gemini models.

### Step 1: Obtain a Free Gemini API Key
1. Visit **[Google AI Studio](https://aistudio.google.com/)**.
2. Sign in with your Google Account.
3. Click on **"Get API key"** in the top navigation or left sidebar.
4. Click **"Create API key"** and choose or create a Google Cloud project.
5. Copy your generated API key (it begins with `AIzaSy...`).

### Step 2: Configure the API Key
You can configure your key in either of two ways:

#### Option A: Via the Web Application (Easiest)
1. Launch the application (`streamlit run app.py`).
2. Navigate to **"7. Settings and API Configuration"** in the sidebar.
3. Under the **"🔑 AI Provider & API Credentials"** tab:
   - Select **Google Gemini (Recommended)**.
   - Paste your API key into the password field.
   - Select your desired model (e.g., `gemini-2.5-flash`).
   - Click **Save Gemini Configuration**.
4. Click **"🔌 Test Gemini Connection"** to verify real-time connectivity.

#### Option B: Via `.env` Environment File
Create or edit the `.env` file in the project root:
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=AIzaSyYourActualKeyHere
```

---

## 2. OpenAI API Setup (Alternative)

If you prefer using OpenAI models (`gpt-4o-mini`, `gpt-4o`):

1. Visit **[OpenAI Platform](https://platform.openai.com/api-keys)**.
2. Sign in and create a new secret key.
3. Add it to your `.env` file:
   ```env
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o-mini
   OPENAI_API_KEY=sk-...
   ```
4. Or configure it directly within the application's **Settings** panel.

---

## 3. Offline Calibrated Demo Mode (No API Key Required)

If you do not have an API key or wish to demonstrate the platform in an offline environment:

1. In the sidebar, open **"7. Settings and API Configuration"**.
2. Select **"Offline Demo Mode (Calibrated Local Mock)"**.
3. Click **"Activate Offline Demo Mode"**.
4. The system will operate with complete realism:
   - Evaluates answer scripts against the rubric.
   - Generates authentic evidence citations and justifications.
   - Computes real BLEU and ROUGE-L similarity scores.
   - Outputs ReportLab PDF marksheets.
   - Marks all results with a clear `[DEMO MODE]` badge.

---

## 4. Security Principles
- **Never Hardcode Keys**: The codebase strictly reads keys from environment variables or safe memory buffers.
- **Obfuscation**: API keys are always masked in the web interface.
- **Git Protection**: `.env` is included in `.gitignore` to prevent accidental commits.
