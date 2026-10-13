
from pathlib import Path
from urllib.request import urlretrieve

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

REPO = "https://huggingface.co/datasets/whoispushkar/cinematch-movie-data/resolve/main"

FILES = [
    "movies_metadata.csv",
    "credits.csv",
    "keywords.csv",
]

for filename in FILES:
    destination = DATA_DIR / filename

    if destination.exists() and destination.stat().st_size > 0:
        print(f"Already downloaded: {filename}")
        continue

    url = f"{REPO}/{filename}"
    print(f"Downloading {filename}...")
    urlretrieve(url, destination)
    print(f"Downloaded {filename}: {destination.stat().st_size:,} bytes")
