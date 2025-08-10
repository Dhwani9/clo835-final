import os
import pathlib
import logging
from urllib.parse import urlparse
from flask import Flask, render_template
from dotenv import load_dotenv

# Load .env for local testing (Kubernetes will set env vars differently)
load_dotenv(override=False)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("app")

app = Flask(__name__)

# -------- Read environment variables --------
APP_NAME = os.getenv("APP_NAME", "My App")
APP_SLOGAN = os.getenv("APP_SLOGAN", "Runs on Kubernetes")
BG_URL = os.getenv("BACKGROUND_IMAGE_URL", "").strip()

# Database creds (from Secret in K8s later)
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_DB = os.getenv("MYSQL_DB", "appdb")
MYSQL_USER = os.getenv("MYSQL_USER", "")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")

# AWS creds (from Secret in K8s later). If not set, we'll use instance role/default chain.
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))

# App port: default 81 (assignment). For local dev in Cloud9, set PORT=8081 before running.
PORT = int(os.getenv("PORT", "81"))

# Local path for background image
BG_LOCAL_DIR = pathlib.Path(app.root_path) / "static" / "bg"
BG_LOCAL_FILE = BG_LOCAL_DIR / "bg.jpg"


# -------- Helper functions --------
def parse_s3_uri(s3_uri: str):
    """Parses s3://bucket/key or https://bucket.s3.<region>.amazonaws.com/key"""
    if not s3_uri:
        raise ValueError("BACKGROUND_IMAGE_URL is empty")
    u = urlparse(s3_uri)
    if u.scheme == "s3":
        return u.netloc, u.path.lstrip("/")
    if u.scheme in ("http", "https") and ".s3" in u.netloc:
        bucket = u.netloc.split(".")[0]
        key = u.path.lstrip("/")
        return bucket, key
    raise ValueError("Invalid S3 URI. Use s3://bucket/key or S3 https URL.")


def get_s3_client():
    """Return a boto3 S3 client. Use explicit keys if provided; else use default creds (instance role, CLI profile, etc.)."""
    import boto3
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        session = boto3.session.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        return session.client("s3")
    # Fallback to default credential chain (Cloud9 instance role, env, config files, etc.)
    return boto3.client("s3", region_name=AWS_REGION)


def download_bg_from_s3() -> bool:
    """Download the background image from S3 into static/bg/bg.jpg"""
    if not BG_URL:
        log.warning("No BACKGROUND_IMAGE_URL provided")
        return False

    log.info("Configured BACKGROUND_IMAGE_URL = %s", BG_URL)
    bucket, key = parse_s3_uri(BG_URL)

    s3 = get_s3_client()
    BG_LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    try:
        log.info("Downloading s3://%s/%s -> %s", bucket, key, BG_LOCAL_FILE)
        s3.download_file(bucket, key, str(BG_LOCAL_FILE))
        if BG_LOCAL_FILE.stat().st_size == 0:
            raise RuntimeError("Downloaded file is empty")
        log.info("Background image downloaded successfully")
        return True
    except Exception as e:
        log.error("Failed to download background image: %s", e)
        return False


# -------- Flask routes --------
@app.route("/")
def index():
    log.info("Serving / with BACKGROUND_IMAGE_URL = %s", BG_URL)
    # Ensure the file exists; if missing (new pod, first run), try to fetch it.
    try:
        if not BG_LOCAL_FILE.exists() or BG_LOCAL_FILE.stat().st_size == 0:
            download_bg_from_s3()
    except Exception as e:
        log.error("Error ensuring background image: %s", e)

    return render_template(
        "index.html",
        app_name=APP_NAME,
        app_slogan=APP_SLOGAN,
        bg_url=BG_URL
    )


if __name__ == "__main__":
    # Try once at startup so the image is ready before serving
    try:
        download_bg_from_s3()
    except Exception as e:
        log.error("Startup download failed: %s", e)

    app.run(host="0.0.0.0", port=PORT)
