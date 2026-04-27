# AI-Financial-Chatbot
💬 AI Financial Chatbot API (IPO, Equity &amp; Bonds)  
An intelligent AI-powered financial assistant backend built with FastAPI + Google Vertex AI (Gemini) that enables users to interactively explore:


📈 IPO data
💰 Equity & Bonds information
🧾 PAN-based investment tracking
🤖 Generative AI chat support

🚀 Key Features
🤖 1. Generative AI Chat (Gemini)
Powered by Google Vertex AI (Gemini 1.5 Flash)
Handles:
Financial queries
General conversation
Cleans responses for better UX

📊 2. IPO Management System
Fetch IPO data from Google Cloud Storage (GCS)
Supports:
Forthcoming IPOs
Current IPOs
Closed IPOs
Displays:
IPO Name
Start & End Dates
Lot Size
Price Band

🧾 3. PAN-Based User Validation
Validates user PAN ID
Fetches user-specific IPO investments
Prevents invalid transactions

💸 4. IPO Investment Simulation
Select IPO
Enter number of lots
Automatically calculates:
✅ Total investment amount

📂 5. Cloud Data Integration
Reads Excel files directly from:
Google Cloud Storage (GCS)
Uses:
pandas for processing
BytesIO for in-memory operations

🎯 6. Menu-Driven Chat Flow
Structured chatbot experience:
Main Menu → Category → Sub-options
Options include:
Bonds
Equity
IPO

🛠️ Tech Stack
Backend: FastAPI
AI Model: Google Vertex AI (Gemini 1.5 Flash)
Cloud Storage: Google Cloud Storage (GCS)
Data Processing: Pandas
Validation: Pydantic
Language: Python

📌 API Endpoint
🔹 Chat API
POST /chat/

📥 Request Body
{
  "id": 3,
  "pan_id": "ABCDE1234F",
  "text": "Tell me about IPO trends",
  "ipo_name": "ABC IPO",
  "lot_count": 2
}

📤 Response Format
{
  "intent": "IPO List",
  "response": "Here are the IPO details...",
  "options": [
    {"id": 13, "name": "Back to IPO Menu"}
  ],
  "ipo_list": [
    {
      "IPO Name": "XYZ IPO",
      "Start Date": "2026-01-01",
      "End Date": "2026-01-05",
      "Lot Size": "50",
      "Price Band": "₹100-120"
    }
  ]
}

⚙️ Setup Instructions
1️⃣ Clone Repository
git clone https://github.com/your-username/financial-chatbot-api.git
cd financial-chatbot-api

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Setup Google Cloud
Enable Vertex AI API
Enable Cloud Storage API
Set credentials:
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"

4️⃣ Update Config
In code:
vertexai.init(project="your-project-id", location="us-central1")
bucket_name = "your-bucket-name"

5️⃣ Run Server
uvicorn app:app --reload

6️⃣ Open API Docs
http://localhost:8000/docs

🧪 How It Works
User selects an option (IPO / Equity / Bonds)
API fetches data from GCS (Excel files)
If needed:
Validates PAN ID
Filters IPO data
Uses Gemini for conversational responses
Returns structured response with options
