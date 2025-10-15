import os
import platform
import zipfile
import urllib.request
from pathlib import Path
import shutil
import sys

# Official BDS URLs
BDS_URLS = {
    "Windows": "https://www.minecraft.net/bedrockdedicatedserver/bin-win/bedrock-server-1.21.113.1.zip",
    "Linux": "https://www.minecraft.net/bedrockdedicatedserver/bin-linux/bedrock-server-1.21.113.1.zip",
}


def ensure_bds_installed(base_path: Path | None = None) -> Path:
    """
    Ensure the Bedrock Dedicated Server is installed locally in ./server/
    next to the user’s Python script (or in a provided base path).
    Returns the path to the server directory.
    """
    # Default: directory of the user's running script
    if base_path is None:
        if getattr(sys, "frozen", False):
            # If packaged as exe
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(sys.argv[0]).resolve().parent

    bds_dir = base_path / "server"
    pack_dir = bds_dir / "development_behavior_packs" / "python_bridge"

    if bds_dir.exists() and (bds_dir / "bedrock_server.exe").exists():
        return bds_dir

    os.makedirs(bds_dir, exist_ok=True)

    system = platform.system()
    url = BDS_URLS.get(system)
    if not url:
        raise RuntimeError(f"Unsupported OS for BDS auto-install: {system}")

    zip_path = base_path / "bds.zip"
    print(f"📦  Downloading Minecraft BDS from {url} …")

    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e:
        print(f"⚠️  Could not download automatically: {e}")
        print("Please manually download the Bedrock Dedicated Server from:")
        print(url)
        print(f"and extract it to: {bds_dir}")
        raise SystemExit(1)

    print("🧩  Extracting server files …")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(bds_dir)
    zip_path.unlink(missing_ok=True)

    print("🪄  Installing Python bridge behaviour pack …")
    src_pack = Path(__file__).parent / "behaviour_pack"
    shutil.copytree(src_pack, pack_dir, dirs_exist_ok=True)

    # Enable content logging
    with open(bds_dir / "server.properties", "a", encoding="utf-8") as f:
        f.write("\ncontent_log_file_enabled=true\n")

    print(f"✅  BDS installation complete at {bds_dir}")
    return bds_dir
