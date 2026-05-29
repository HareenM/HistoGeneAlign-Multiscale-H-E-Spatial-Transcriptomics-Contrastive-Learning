# I am downloading just a sample of the data, specifically the TENX95 sample which is also used in the official example

from pathlib import Path
from huggingface_hub import snapshot_download

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[1]

RAW_DIR = REPO_ROOT / "data" / "raw" / "hest"
RAW_DIR.mkdir(parents=True, exist_ok=True)

repo_id = "MahmoodLab/hest"

target_files = [
    "metadata/TENX95.json",
    "st/TENX95.h5ad",
    "patches/TENX95.h5",
    "wsis/TENX95.tif",
    "thumbnails/TENX95_downscaled_fullres.jpeg",
    "spatial_plots/TENX95_spatial_plots.png",
    "patches_vis/TENX95_patch_vis.jpg",
    "pixel_size_vis/TENX95_pixel_size_vis.png",
]

print("Repository root:", REPO_ROOT)
print("Download directory:", RAW_DIR)
print("Files to download:")

for f in target_files:
    print(" -", f)

snapshot_download(
    repo_id=repo_id,
    repo_type="dataset",
    local_dir=str(RAW_DIR),
    allow_patterns=target_files,
    local_dir_use_symlinks=False,
)

print("\nDownload complete.")

downloaded_files = [p for p in RAW_DIR.rglob("*") if p.is_file()]

print("Total downloaded files:", len(downloaded_files))

for p in downloaded_files:
    size_mb = p.stat().st_size / (1024 ** 2)
    print(f"{p.relative_to(RAW_DIR)} | {size_mb:.2f} MB")