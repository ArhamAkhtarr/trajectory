import io
import logging
import os
import uuid
import docx
import httpx
import pdfplumber
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)


def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    fn_lower = (filename or "").lower()

    if not file_bytes:
        raise HTTPException(
            status_code=422,
            detail="Uploaded file is empty. Please upload a valid resume.",
        )

    text = ""
    if fn_lower.endswith(".pdf"):
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        pages_text.append(extracted)
                text = "\n".join(pages_text).strip()
        except Exception as e:
            logger.error(f"Failed to parse PDF resume: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Corrupt or unreadable PDF file: {str(e)}",
            )

    elif fn_lower.endswith(".docx") or fn_lower.endswith(".doc"):
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs).strip()
        except Exception as e:
            logger.error(f"Failed to parse DOCX resume: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Corrupt or unreadable Word document: {str(e)}",
            )
    else:
        raise HTTPException(
            status_code=422,
            detail="Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx).",
        )

    if not text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from file. The document may be empty or unreadable.",
        )

    return text


async def upload_file_to_supabase(
    user_id: str,
    file_ref_id: str,
    filename: str,
    file_bytes: bytes,
    content_type: str | None,
) -> str:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv(
        "SUPABASE_PUBLISHABLE_KEY"
    )

    bucket = "resumes"
    safe_filename = filename.replace(" ", "_")
    storage_path = f"{user_id}/{file_ref_id}_{safe_filename}"

    if not supabase_url or not supabase_key:
        logger.warning(
            "Supabase credentials missing, skipping storage API upload."
        )
        return storage_path

    url = f"{supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{storage_path}"
    headers = {
        "Authorization": f"Bearer {supabase_key}",
        "apikey": supabase_key,
        "Content-Type": content_type or "application/octet-stream",
        "x-upsert": "true",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, content=file_bytes, headers=headers)
            if res.status_code == 404:
                # Create bucket if it doesn't exist
                create_bucket_url = (
                    f"{supabase_url.rstrip('/')}/storage/v1/bucket"
                )
                await client.post(
                    create_bucket_url,
                    json={"id": bucket, "name": bucket, "public": False},
                    headers=headers,
                )
                res = await client.post(url, content=file_bytes, headers=headers)

            if res.status_code in (200, 201):
                logger.info(
                    f"Uploaded resume to Supabase Storage: {storage_path}"
                )
            else:
                logger.warning(
                    f"Supabase Storage upload returned status {res.status_code}: {res.text}"
                )
    except Exception as e:
        logger.error(f"Error uploading file to Supabase Storage: {e}")

    return storage_path
