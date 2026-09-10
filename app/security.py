import os
import re
from functools import wraps
from pathlib import Path

import bleach
import pyotp
from cryptography.fernet import Fernet, InvalidToken
from flask import abort, current_app
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

ALLOWED_TAGS = []
ALLOWED_ATTRIBUTES = {}

# Allowed upload types: { extension: (description, content-signature matchers) }
ALLOWED_UPLOAD_TYPES = {
    ".pdf": ("PDF document", ((b"%PDF", None),)),
    ".png": ("PNG image", ((b"\x89PNG\r\n\x1a\n", None),)),
    ".jpg": ("JPEG image", ((b"\xff\xd8\xff", None),)),
    ".jpeg": ("JPEG image", ((b"\xff\xd8\xff", None),)),
    ".txt": ("Text file", ((None, None),)),
}

def hash_password(password: str) -> str:
    return generate_password_hash(password, method="scrypt")

def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)

def sanitize_text(value: str, max_length: int = 200) -> str:
    value = (value or "").strip()
    value = bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return value[:max_length]

def validate_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""))

def validate_password(password: str) -> bool:
    if not password or len(password) < 10 or len(password) > 128:
        return False
    return bool(re.search(r"[A-Z]", password) and re.search(r"[a-z]", password)
                and re.search(r"\d", password) and re.search(r"[^A-Za-z0-9]", password))

def get_fernet() -> Fernet:
    key = os.getenv("FERNET_KEY")
    if not key:
        raise RuntimeError("FERNET_KEY is not configured.")
    return Fernet(key.encode())

def encrypt_value(value: str | None) -> str | None:
    if value is None:
        return None
    return get_fernet().encrypt(value.encode()).decode()

def decrypt_value(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return get_fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return "[unavailable]"

def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator

def safe_upload_filename(filename: str) -> str:
    clean = secure_filename(filename)
    if not clean:
        raise ValueError("Invalid filename.")
    return clean

def validate_upload_file(filename: str, file_stream) -> str:
    """Validate a file upload by extension whitelist and content signature.

    Returns the sanitized filename on success, raises ValueError otherwise.
    """
    clean = safe_upload_filename(filename)
    ext = Path(clean).suffix.lower()
    if ext not in ALLOWED_UPLOAD_TYPES:
        raise ValueError("File type not allowed.")
    if ext == ".txt":
        return clean

    signature = file_stream.read(16)
    file_stream.seek(0)
    for magic, _ in ALLOWED_UPLOAD_TYPES[ext][1]:
        if magic is None:
            continue
        if not signature.startswith(magic):
            raise ValueError("File content does not match its extension.")
    return clean

def safe_upload_path(filename: str) -> Path:
    clean = safe_upload_filename(filename)
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    destination = (upload_dir / clean).resolve()
    if not destination.is_relative_to(upload_dir) or destination == upload_dir:
        raise ValueError("Unsafe upload path.")
    return destination


def generate_totp_secret() -> str:
    """Generate a new Base32 TOTP secret."""
    return pyotp.random_base32()

def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a TOTP code with a 30-second window tolerance of 1 step."""
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)

def totp_provisioning_uri(secret: str, email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="SecureStock")
