"""Production entry point using the waitress WSGI server.

Usage:
    python serve.py
"""
import os
from waitress import serve
from wsgi import app

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    threads = int(os.getenv("WAITRESS_THREADS", "4"))
    print(f"Serving SecureStock on http://{host}:{port}")
    serve(app, host=host, port=port, threads=threads)