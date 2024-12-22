
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import pandas as pd
from table import main_func

app = FastAPI()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
@app.post("/process/")
async def extract_table(
    request: Request,
    pdf_file: UploadFile = File(...),
    csv_file: UploadFile = File(...)
):
    print("process")
    pdf_path = os.path.join(UPLOAD_DIR, pdf_file.filename)
    print(pdf_path)
    csv_path = os.path.join(UPLOAD_DIR, csv_file.filename)
    with open(pdf_path, "wb") as buffer:
        buffer.write(pdf_file.file.read())
    with open(csv_path, "wb") as buffer:
        buffer.write(csv_file.file.read())
    headers_df = pd.read_csv(csv_path,encoding="utf-8")
    headers = [header for header in headers_df[headers_df.columns[0]]]
  
    final_df = main_func(pdf_path,headers)
    if type(final_df)!=str:
        output_csv_path = os.path.join(UPLOAD_DIR, "final_df.csv")
        final_df.to_csv(output_csv_path, index=False)
        return templates.TemplateResponse(
            "res.html",
            {"request": request, "download_url": f"/download/final_df.csv"}
    )
    else:
        return templates.TemplateResponse(
            "res.html",
            {"request":request,"Data not sound":"No data found"}
    )


@app.get("/download/{file_name}")
async def download_file(file_name: str):
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}
if __name__== "__main__":
    uvicorn.run("main2:app")