📄 Resume Processor API
A FastAPI application that processes PDF resumes using a Language Model (LLM) like OpenAI's GPT, compares them against a provided job requirement, and generates an Excel file with structured analysis.

✨ Features
Upload one or more PDF resumes.

Provide a text description of your job requirement.

Uses an LLM to analyze resumes and extract key information:

Name

Years of Experience

Key Strengths

Summary

Fit for the Role (Y/N)

Overfit for the Role (Y/N)

Returns a downloadable Excel (.xlsx) file with the results.

🚀 How to Run Locally
Clone the Repository

bash
Copy
Edit
git clone <your-repo-url>
cd <your-repo-name>
Install Dependencies

bash
Copy
Edit
pip install fastapi uvicorn openai pandas openpyxl
Set Environment Variables Make sure you set your LLM API key:

bash
Copy
Edit
export OPEN_API_KEY=your-openai-api-key
Run the Application

bash
Copy
Edit
uvicorn main:app --reload --port 8000
Access the API Docs Navigate to:

bash
Copy
Edit
http://localhost:8000/docs
📂 API Endpoints
POST /process_resumes_to_excel/
Upload PDF files and requirement text. Returns an Excel file with the extracted information.

Form Fields:

files: One or more resume files (PDF only).

requirement_text: The job description or requirement text.

Response:

Excel file (resume_analysis_results.xlsx) for download.

GET /
Simple health-check endpoint.

Response:

json
Copy
Edit
{
  "message": "Resume Processing API is running."
}
🛠️ Internals
FastAPI: Web framework.

Pandas: For generating Excel sheets.

OpenAI (or compatible LLM client): To extract structured data from resumes.

Concurrency: Uses asyncio to handle multiple uploads efficiently.

Security: API keys should be set via environment variables.

📌 Notes
LLM Client: The code assumes usage of OpenAI's API. Replace the client initialization if you are using a different LLM provider.

File Size Limit: Make sure your LLM can handle large base64-encoded PDFs or preprocess them accordingly.

Format Expectation: The LLM is expected to return a dictionary with specific keys in its response.

Example required dictionary format:

python
Copy
Edit
{
  'NAME': 'John Doe',
  'YEARS OF EXPERIENCE': '5',
  'KEY STRENGTHS': ['Python', 'Data Analysis'],
  'SUMMARY': 'Experienced data analyst...',
  'SUITABLE FOR MY REQUIREMENT (Y/N)': 'Y',
  'OVERFIT (Y/N)': 'N'
}
🧹 Future Improvements
Add OCR/Text extraction before sending to LLM for better token efficiency.

Implement retries/backoff for LLM API failures.

Add authentication for production deployments.

Improve error reporting with detailed logs.

🤝 Contributions
Feel free to open issues or submit pull requests if you find ways to improve this project!

📜 License
This project is licensed under the MIT License (or your preferred license).

Would you also like me to generate a requirements.txt for you based on the imports? 🚀
It'll make setup even easier! 🎯
