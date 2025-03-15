from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

import os
import uuid
from main import main  # Import the main function

app = FastAPI()

# Temporary directory to store uploaded and translated files
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def upload_form():
    return """
    <html>
        <head>
            <title>XLIFF Translator</title>
        </head>
        <body>
            <h1>Upload XLIFF File for Translation</h1>
            <form action="/translate/" method="post" enctype="multipart/form-data">
                <label for="file">Choose XLIFF file:</label>
                <input type="file" name="file" id="file" accept=".xlf,.xliff"><br><br>
                <label for="language">Target Language:</label>
                <input type="text" name="language" id="language" placeholder="e.g., fr, es, de"><br><br>
                <button type="submit">Translate and Download</button>
            </form>
        </body>
    </html>
    """


@app.post("/translate/")
async def translate_file(file: UploadFile = File(...), language: str = "en"):
    # Save the uploaded file to a temporary location
    upload_path = os.path.join(TEMP_DIR, f"upload_{uuid.uuid4()}.xlf")
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    # Define the output path for the translated file
    output_path = os.path.join(TEMP_DIR, f"translated_{uuid.uuid4()}.xlf")

    # Call the main function with the required arguments
    main(source_path=upload_path, destination_path=output_path, language=language)

    # Return the translated file as a downloadable response
    return FileResponse(
        output_path,
        filename=f"translated_{file.filename}",
        media_type="application/x-xliff+xml",
    )


@app.on_event("shutdown")
def cleanup_temp_files():
    """Clean up temporary files on application shutdown."""
    for filename in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)