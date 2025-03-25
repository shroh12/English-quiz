from pathlib import Path

wORK_DIR = Path(__file__).parent
IMG_DIR, IN_DIR, OUT_DIR = wORK_DIR / "img", wORK_DIR / "input", wORK_DIR / "output"

if __name__ == "__main__":
    IMG_DIR.mkdir(exist_ok=True)
    IN_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)