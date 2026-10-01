"""Download the pinned research sources; never execute downloaded code."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "60cd5b7530eb954b02ae94da967111f5b5c3c01b"
REPO = "hamrel-cxu/EnbPI"


def download(url, target):
    request = Request(url, headers={"User-Agent": "EnbPI-portfolio-reproduction"})
    with urlopen(request, timeout=90) as response:
        payload = response.read()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    print(f"Saved {target.relative_to(ROOT)} ({len(payload):,} bytes)", flush=True)
    return {"url": url, "path": target.relative_to(ROOT).as_posix(),
            "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def main():
    records = []
    vendor = ROOT / "references" / "upstream"
    tree_url = f"https://api.github.com/repos/{REPO}/git/trees/{COMMIT}?recursive=1"
    records.append(download(tree_url, ROOT / "references" / "upstream-tree.json"))
    tree = json.loads((ROOT / "references" / "upstream-tree.json").read_text())
    paths = ["LICENSE", "README.md", "PI_class_EnbPI.py", "utils_EnbPI.py", "tests_paper.py"]
    paths += [entry["path"] for entry in tree["tree"]
              if entry["path"].startswith("Results/")
              and "Solar_Atl" in entry["path"]
              and "many_alpha" in entry["path"]
              and entry["path"].endswith(".csv")]
    paths.append("Data/Solar_Atl_data.csv")
    for path in paths:
        target = ROOT / "data" / "raw" / "Solar_Atl_data.csv" if path.startswith("Data/") else vendor / path
        records.append(download(f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{path}", target))
    records.append(download("https://proceedings.mlr.press/v139/xu21h/xu21h.pdf",
                            ROOT / "references" / "xu-xie-2021-enbpi.pdf"))
    manifest = {"repository": f"https://github.com/{REPO}", "commit": COMMIT,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "files": records}
    (ROOT / "references" / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
