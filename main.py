import os
import io
import base64
import re
import ast  # For safe evaluation of literal structures
import asyncio
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
from dotenv import load_dotenv
import logging
load_dotenv()
# --- LLM Client Initialization ---
# IMPORTANT: Replace this with your actual client initialization
# Ensure API keys are handled securely (e.g., environment variables)
try:
    # Example using OpenAI client - replace with your actual client library
    from openai import OpenAI, APIConnectionError
    logging.info("Get OpenAI token from environment...")
    client = OpenAI(
        api_key= os.environ.get("OPEN_API_KEY") # Good practice
    )
    print(os.environ.get("OPENAI_API_KEY"))
    # Perform a simple check if possible (optional)
    # client.models.list()
    print("LLM Client Initialized.")
except ImportError:
    print("Error: OpenAI library not found. Please install it (`pip install openai`) or replace with your client.")
    client = None # Set client to None to indicate failure
except APIConnectionError as e:
    print(f"Error: Could not connect to LLM API: {e}")
    client = None
except Exception as e:
    print(f"Error initializing LLM Client: {e}")
    client = None

# --- Your Helper Functions (Slightly Modified) ---

def extract_python_dict_string(response_text: str) -> str | None:
    """
    Finds the first Python dictionary string within potentially surrounding text or code blocks.
    Adjust the regex if your LLM's output format is different.
    """
    # Try finding dict within python code blocks first
    match = re.search(r'```python\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If not in code block, try finding a raw dictionary structure
    # This regex is basic, might need refinement depending on LLM output variation
    match = re.search(r'(\{.*?\})', response_text, re.DOTALL)
    if match:
        # Be cautious, this might grab JSON-like structures not meant to be the primary dict
        # Check if it looks like the expected dict (e.g., contains specific keys)
        potential_dict_str = match.group(1).strip()
        # Add a simple heuristic check - adjust as needed
        if "'NAME':" in potential_dict_str and "'SUMMARY':" in potential_dict_str:
             return potential_dict_str

    print(f"Warning: Could not extract a dictionary string matching expected patterns from LLM output: {response_text[:200]}...")
    return None

async def process_single_resume(
    file_bytes: bytes,
    filename: str,
    requirement_text: str,
    llm_client: Any # Use Any type hint or your specific client type
) -> Dict[str, Any] | None:
    """
    Processes a single resume (provided as bytes) using the LLM client.
    Returns the extracted dictionary or None if processing fails.
    Runs the blocking LLM call in a separate thread.
    """
    if not llm_client:
        raise HTTPException(status_code=500, detail="LLM Client is not initialized.")

    base64_string = base64.b64encode(file_bytes).decode("utf-8")

    try:
        # Run the synchronous client call in a thread to avoid blocking asyncio event loop
        response = await asyncio.to_thread(
            llm_client.responses.create, # Assuming OpenAI's chat structure, adjust if needed
            model="gpt-4o-mini", # or your preferred model
            input=[ # Using messages API which is more standard now
                {
                    "role": "user",
                    "content": [
                        # Note: Sending files directly might be possible with some APIs,
                        # but base64 is common. Check your client's documentation.
                        # This structure assumes a multimodal model or API handling base64.
                        # If your model only takes text, you'd extract text first.
                        # Placeholder for image if needed, adjust for actual API
                        # {"type": "image_url", "image_url": {"url": f"data:application/pdf;base64,{base64_string}"}},
                        # Send content via text, maybe after extracting text from PDF
                        {"type": "input_file","filename": f"Processing resume: {filename}", "file_data": f"data:application/pdf;base64,{base64_string}"},
                        {"type": "input_text", "text": requirement_text + ''' Please go through the resume and tell me if the candidate is a good fit for the role. I want the output to be a single python dictionary. The format I want is
                        {'NAME': '...', "YEARS OF EXPERIENCE": '...', 'KEY STRENGTHS': ['...', '...'], 'SUMMARY': '...', 'SUITABLE FOR MY REQUIREMENT (Y/N)': 'Y/N', 'OVERFIT (Y/N)': 'Y/N'}. The Dictionary keys MUST be exactly as shown. The values should be the information extracted from the resume or your assessment.'''}
                    ],
                },
            ]
        )
        # Adjust response parsing based on your specific client library
        response_text = response.output_text # If using older completion style
        # response_text = response.choices[0].message.content

    except Exception as e:
        print(f"Error calling LLM for {filename}: {e}")
        # Return None or a specific error structure if needed
        return {"ERROR": f"LLM API call failed for {filename}: {e}"}

    # --- Safely parse the response ---
    dict_string = extract_python_dict_string(response_text)
    if not dict_string:
         print(f"Error: Could not extract dictionary string from LLM response for {filename}.")
         return {"ERROR": f"Could not parse LLM response for {filename}"}

    try:
        # Use ast.literal_eval for safety instead of eval()
        extracted_data = ast.literal_eval(dict_string)
        if not isinstance(extracted_data, dict):
             raise ValueError("Parsed result is not a dictionary.")
        # Add filename for reference
        extracted_data['FILENAME'] = filename
        return extracted_data
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing dictionary string for {filename}: {e}")
        print(f"Raw response text was: {response_text}")
        return {"ERROR": f"Could not parse dictionary from LLM response for {filename}"}
    except Exception as e:
         print(f"Unexpected error parsing dictionary for {filename}: {e}")
         return {"ERROR": f"Unexpected parsing error for {filename}"}


# --- FastAPI App ---
app = FastAPI(
    title="Resume Processor to Excel",
    description="Upload resumes (PDFs) and requirements to get an Excel analysis.",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://resume-shortlist-ui.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(
    "/process_resumes_to_excel/",
    response_class=StreamingResponse,
    summary="Process Resumes and Requirements to Excel",
    description="Upload one or more PDF resumes and provide requirement text. Returns an Excel file with extracted details.",
    tags=["Resume Processing"]
)
async def process_resumes_endpoint(
    files: List[UploadFile] = File(..., description="One or more PDF resume files."),
    requirement_text: str = Form(..., description="Text describing the job requirements."),
):
    """
    Endpoint to process uploaded PDF resumes against requirements.
    """
    if client is None:
         raise HTTPException(status_code=500, detail="LLM Client is not available or failed to initialize.")

    processed_results = []
    tasks = []

    for file in files:
        if file.content_type != "application/pdf":
            print(f"Skipping non-PDF file: {file.filename} ({file.content_type})")
            processed_results.append({
                "FILENAME": file.filename,
                "ERROR": "Invalid file type (must be PDF)"
            })
            continue

        if not file.filename:
            print("Skipping file with no filename.")
            processed_results.append({
                "FILENAME": "N/A",
                "ERROR": "File uploaded without a filename"
            })
            continue

        print(f"Processing file: {file.filename}")
        try:
            file_bytes = await file.read()
            if not file_bytes:
                 print(f"Skipping empty file: {file.filename}")
                 processed_results.append({"FILENAME": file.filename, "ERROR": "Empty file uploaded"})
                 continue

            # Create an asyncio task for each resume processing
            tasks.append(
                process_single_resume(
                    file_bytes=file_bytes,
                    filename=file.filename,
                    requirement_text=requirement_text,
                    llm_client=client
                )
            )
        except Exception as e:
            print(f"Error reading file {file.filename}: {e}")
            processed_results.append({"FILENAME": file.filename, "ERROR": f"Failed to read file: {e}"})
        finally:
            await file.close() # Ensure file handle is closed

    # Run all processing tasks concurrently
    if tasks:
        results_from_tasks = await asyncio.gather(*tasks)
        # Filter out None results if process_single_resume returns None on error
        processed_results.extend([res for res in results_from_tasks if res is not None])


    # --- Generate Excel/CSV in Memory ---
    if not processed_results:
        raise HTTPException(status_code=400, detail="No valid resumes processed or processing failed for all files.")

    try:
        df = pd.DataFrame(processed_results)

        # Reorder columns to put FILENAME and ERROR first if they exist
        cols = df.columns.tolist()
        preferred_order = ['FILENAME', 'ERROR', 'NAME', 'YEARS OF EXPERIENCE', 'KEY STRENGTHS', 'SUMMARY', 'SUITABLE FOR MY REQUIREMENT (Y/N)', 'OVERFIT (Y/N)']
        new_cols = [col for col in preferred_order if col in cols] + [col for col in cols if col not in preferred_order]
        df = df[new_cols]


        output_buffer = io.BytesIO()
        # Use Excel format (.xlsx)
        await asyncio.to_thread(df.to_excel, output_buffer, index=False, engine='openpyxl')
        media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        output_filename = "resume_analysis_results.xlsx"

        # --- OR Use CSV format (.csv) ---
        # await asyncio.to_thread(df.to_csv, output_buffer, index=False, encoding='utf-8')
        # media_type = 'text/csv'
        # output_filename = "resume_analysis_results.csv"

        output_buffer.seek(0)

    except Exception as e:
        print(f"Error creating Excel/CSV file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate output file: {e}")

    # --- Prepare and Return Response ---
    headers = {
        'Content-Disposition': f'attachment; filename="{output_filename}"'
    }
    return StreamingResponse(
        output_buffer,
        media_type=media_type,
        headers=headers
    )

# --- Optional: Root endpoint ---
@app.get("/", tags=["Status"])
async def read_root():
    return {"message": "Resume Processing API is running."}

# --- How to Run ---
# Save as main.py
# Run: uvicorn main:app --reload --port 8000 