# Resume Processing API

This FastAPI backend service processes uploaded PDF resumes against provided job requirements using an LLM (Large Language Model, e.g., GPT-4o-mini). It extracts key information based on a specified format and returns the results compiled into a single Excel (`.xlsx`) file.

## Features

*   **Multiple Resume Upload:** Accepts one or more PDF files via multipart/form-data.
*   **Requirement Input:** Takes job requirement text as input alongside the resumes.
*   **LLM Integration:** Uses a configured LLM client (e.g., OpenAI) to analyze resume content against requirements.
*   **Structured Extraction:** Prompts the LLM to return data in a specific Python dictionary format.
*   **Safe Parsing:** Uses `ast.literal_eval` to safely parse the dictionary string from the LLM response, preventing arbitrary code execution risks associated with `eval()`.
*   **Concurrent Processing:** Processes multiple resumes concurrently using `asyncio` for better performance.
*   **Excel Output:** Generates an Excel (`.xlsx`) file containing the extracted information for all processed resumes.
*   **Error Handling:** Includes basic handling for invalid file types, LLM API errors, and parsing failures, reporting errors within the output Excel file.

## Requirements

*   Python 3.8+
*   pip (Python package installer)
*   An LLM API key and a configured client (e.g., OpenAI Python client).

## Setup and Installation

1.  **Clone or Download:** Get the project code (`main.py` and this README).
    ```bash
    # If using git
    # git clone <repository_url>
    # cd <repository_directory>
    ```

2.  **Create Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install fastapi uvicorn pandas "python-multipart" openpyxl openai
    ```
    *Note: Replace `openai` with the specific library required for your LLM client if you are not using OpenAI.*

## Configuration

1.  **LLM Client Initialization:**
    *   Open the `main.py` file.
    *   Locate the section marked `# --- LLM Client Initialization ---`.
    *   **Replace the placeholder code** with the actual initialization logic for your LLM client (e.g., `client = OpenAI(...)`).

2.  **API Keys:**
    *   **Crucially, handle your LLM API key securely.** Do not hardcode it directly in `main.py`.
    *   **Recommended Method:** Use environment variables. Set the environment variable before running the application:
        ```bash
        # On macOS/Linux
        export YOUR_LLM_API_KEY='your-actual-api-key'
        # On Windows (Command Prompt)
        set YOUR_LLM_API_KEY=your-actual-api-key
        # On Windows (PowerShell)
        $env:YOUR_LLM_API_KEY="your-actual-api-key"
        ```
    *   Modify the client initialization in `main.py` to read the key from the environment variable (e.g., `api_key=os.environ.get("YOUR_LLM_API_KEY")`). Ensure you `import os`.

## Running the API

Once dependencies are installed and configuration is done, run the FastAPI application using Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000


main:app: Tells Uvicorn to find the app object inside the main.py file.
--reload: Enables auto-reloading when code changes (useful for development). Remove this flag for production.
--host 0.0.0.0: Makes the server accessible on your network. Use 127.0.0.1 for local access only.
--port 8000: Specifies the port to run on.
The API will be available at http://<your-server-ip>:8000.
Usage
Endpoint: Process Resumes
URL: /process_resumes_to_excel/
Method: POST
Request Body Type: multipart/form-data
Parameters:
files: One or more file parts, each containing a PDF resume. The field name for each file must be files.
requirement_text: A string containing the job requirements description. This should be sent as a form data field.
Success Response:
HTTP Status Code: 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Body: The generated Excel file (.xlsx) as a downloadable attachment (e.g., resume_analysis_results.xlsx).
Error Responses:
400 Bad Request: Invalid input (e.g., non-PDF file uploaded, empty file, failed to read file, no text extractable if that check is enabled).
422 Unprocessable Entity: LLM response couldn't be parsed into the expected dictionary format.
500 Internal Server Error: LLM client not initialized, LLM API call failed, failed to generate Excel file, or other unexpected server errors.
(Responses are standard FastAPI JSON error formats).

Example Request
curl -X POST "http://localhost:8000/process_resumes_to_excel/" \
  -H "accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@/path/to/your/resume1.pdf" \
  -F "files=@/path/to/your/resume2.pdf" \
  -F "requirement_text=Seeking a Data Scientist with 3+ years experience in Python, SQL, and machine learning frameworks like Scikit-learn and TensorFlow." \
  --output analysis_results.xlsx
  (Replace /path/to/your/resumeX.pdf with actual file paths and adjust the requirement_text.)


Root Endpoint
URL: /
Method: GET
Description: A simple endpoint to check if the API is running.
Response: {"message": "Resume Processing API is running."}
Output Excel Format
The generated Excel file (.xlsx) will contain one row for each successfully processed (or attempted) resume. The columns typically include:
FILENAME: The original filename of the uploaded PDF.
ERROR: Contains an error message if processing failed for that specific file (e.g., "Invalid file type", "LLM API call failed", "Could not parse LLM response"). This column might be empty on success.
NAME: Extracted candidate name.
YEARS OF EXPERIENCE: Extracted years of experience.
KEY STRENGTHS: List of key strengths identified.
SUMMARY: A summary of the candidate's profile relevant to the requirements.
SUITABLE FOR MY REQUIREMENT (Y/N): LLM's assessment (Yes/No).
OVERFIT (Y/N): LLM's assessment (Yes/No).
(Note: The exact columns depend on the successful parsing of the dictionary returned by the LLM. The order might include FILENAME and ERROR first for clarity.)
Important Notes
LLM Dependency: The quality and format of the results heavily depend on the capabilities of the configured LLM and the clarity of the prompt provided in process_single_resume. You may need to tune the prompt for optimal results with your specific LLM and use case.
PDF Content: The current implementation sends the PDF content as a base64 encoded string to the LLM. This relies on the LLM being able to interpret this format (common for multimodal models). If your LLM requires plain text, you would need to modify process_single_resume to first extract text from the PDF bytes (e.g., using pypdf) before sending it to the LLM.
Security: Always handle API keys securely using environment variables or a proper secrets management system. The use of ast.literal_eval significantly improves security over eval, but be aware that LLM output parsing always carries some level of risk if the LLM output format isn't strictly controlled.
Scalability: Processing is done concurrently, but reading entire files into memory and base64 encoding might become a bottleneck for very large files or extremely high request volumes. Consider streaming approaches if this becomes an issue.
