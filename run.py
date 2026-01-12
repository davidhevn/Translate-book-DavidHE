"""Simple run script - just execute this file to start the app."""
import subprocess
import sys

def main():
    print("=" * 50)
    print("📚 Book Translator - English to Vietnamese")
    print("=" * 50)
    print()
    print("Starting server...")
    print("Open your browser at: http://localhost:8000")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Run uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000",
        "--reload"
    ])

if __name__ == "__main__":
    main()
