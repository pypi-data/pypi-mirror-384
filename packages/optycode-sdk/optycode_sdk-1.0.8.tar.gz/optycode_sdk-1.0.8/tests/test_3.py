import json
from supabase import create_client
import os
from dotenv import load_dotenv
import uuid
load_dotenv()

SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxjdHJpb29vdmdqamlnbmJ1Z2xnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzQ0ODg1OCwiZXhwIjoyMDczMDI0ODU4fQ.jZrBYhGwBoKrr8hyKC1XpRb6ws1ti9YDA86yhsF_les"

SUPABASE_URL = "https://lctriooovgjjignbuglg.supabase.co"
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
token = 'abc'

def handler(event, context):
    """
    Generate a presigned upload URL for a file without any prior info.
    """
    try:
        # Generate a fully random temporary path
        random_key = str(uuid.uuid4())
        temp_path = f"tmp/{random_key}"  # no filename, no user_id needed

        # Generate presigned URL valid for 2 hours (default duration)
        signed_url = supabase.storage.from_("uploads").create_signed_upload_url(temp_path)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "upload_url": signed_url,
                "expires_in": 7200,  # 2 hours
                "temp_path": temp_path
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

event = {}
context = {}
response = handler(event, context)
print(response)