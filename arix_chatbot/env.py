from pathlib import Path
from dotenv import load_dotenv

# Find the project root (where this file lives)
ROOT = Path(__file__).parent
dotenv_path = ROOT / ".env"

if dotenv_path.exists():
    load_dotenv(dotenv_path)
