#!/usr/bin/env python3

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
from dotenv import load_dotenv

from . import __version__

load_dotenv()

DATASET_ID = "gd_lk56epmy2i5g7lzu0k"
TRIGGER_URL = (
    f"https://api.brightdata.com/datasets/v3/trigger"
    f"?dataset_id={DATASET_ID}&notify=false&include_errors=true"
)
PROGRESS_URL = "https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
SNAPSHOT_URL = "https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
POLL_INTERVAL = 10  # seconds between status checks
DEFAULT_OUTPUT_DIR = "Downloads"
DEFAULT_RESULT_DIR = "Result"
CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def parse_youtube_input(raw: str) -> str:
    """Return a canonical YouTube watch URL given a URL or bare video ID."""
    raw = raw.strip()
    if "youtu.be" in raw:
        video_id = urlparse(raw).path.lstrip("/").split("?")[0]
    elif "youtube.com" in raw:
        qs = parse_qs(urlparse(raw).query)
        video_id = (qs.get("v") or [None])[0]
        if not video_id:
            raise ValueError(f"Cannot extract video ID from URL: {raw}")
    else:
        video_id = raw  # assume bare ID like EJYaiqV-pvs

    return f"https://www.youtube.com/watch?v={video_id}"


def next_output_number(folder: Path) -> int:
    """Return the next unused youtube_<n> number in folder."""
    numbers = []
    for f in folder.glob("youtube_*.json"):
        try:
            numbers.append(int(f.stem.split("_")[1]))
        except (IndexError, ValueError):
            pass
    return max(numbers, default=0) + 1


def trigger_scrape(api_key: str, urls: list) -> str:
    """POST to Brightdata trigger endpoint and return the snapshot_id."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = json.dumps({
        "input": [
            {"url": url, "country": "", "transcription_language": ""}
            for url in urls
        ]
    })
    resp = requests.post(TRIGGER_URL, headers=headers, data=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    snapshot_id = data.get("snapshot_id")
    if not snapshot_id:
        raise RuntimeError(f"No snapshot_id in trigger response: {data}")
    return snapshot_id


def poll_until_ready(api_key: str, snapshot_id: str, timeout: int) -> None:
    """Poll progress endpoint until status is 'ready' or timeout is reached."""
    headers = {"Authorization": f"Bearer {api_key}"}
    url = PROGRESS_URL.format(snapshot_id=snapshot_id)
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "unknown")
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] status: {status}", flush=True)

        if status == "ready":
            return
        if status in ("failed", "error"):
            raise RuntimeError(f"Snapshot {snapshot_id} failed: {data}")

        remaining = deadline - time.monotonic()
        time.sleep(min(POLL_INTERVAL, max(0, remaining)))

    raise TimeoutError(f"Snapshot not ready after {timeout}s")


def extract_results(source_path: Path, result_dir: Path) -> list:
    """Read a raw snapshot JSON and write one slim file per video into result_dir."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    folder = result_dir / date_str
    folder.mkdir(parents=True, exist_ok=True)

    items = json.loads(source_path.read_text(encoding="utf-8"))
    saved = []
    for item in items:
        video_id = item.get("video_id") or item.get("shortcode")
        if not video_id:
            continue
        slim = {
            "url": item.get("url"),
            "title": item.get("title"),
            "youtuber": item.get("youtuber"),
            "handle_name": item.get("handle_name"),
            "transcript": item.get("transcript"),
        }
        out = folder / f"{video_id}.json"
        out.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")
        saved.append(out)
    return saved


def download_snapshot(api_key: str, snapshot_id: str, output_path: Path) -> None:
    """Download the finished snapshot JSON to output_path."""
    headers = {"Authorization": f"Bearer {api_key}"}
    url = SNAPSHOT_URL.format(snapshot_id=snapshot_id)
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(resp.text, encoding="utf-8")


def main():
    print(f"Brightdata API Scraper version {__version__}")
    parser = argparse.ArgumentParser(
        prog="python -m scraper",
        description="Download YouTube video data via the Brightdata scraping API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Input can be YouTube watch URLs or bare video IDs, mixed freely:

  python -m scraper EJYaiqV-pvs b6tPIquUMSA
  python -m scraper https://www.youtube.com/watch?v=EJYaiqV-pvs
  python -m scraper https://youtu.be/EJYaiqV-pvs EJYaiqV-pvs
  python -m scraper --file urls.txt
  cat urls.txt | python -m scraper --file -

Output is saved to:
  ~/Downloads/<YYYY-MM-DD>/youtube_<n>.json

The number <n> is auto-incremented so parallel invocations never overwrite each other.
""",
    )
    parser.add_argument(
        "urls",
        nargs="*",
        metavar="URL_OR_ID",
        help="YouTube watch URLs or video IDs (e.g. EJYaiqV-pvs)",
    )
    parser.add_argument(
        "--file", "-f",
        metavar="FILE",
        help="File with one URL or ID per line; use - to read from stdin",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        metavar="SECONDS",
        help="Max seconds to wait for Brightdata to finish (default: 600)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help="Base directory for raw snapshots (overrides config.json; default: Downloads)",
    )
    parser.add_argument(
        "--result-dir",
        default=None,
        metavar="DIR",
        help="Base directory for extracted results (overrides config.json; default: Result)",
    )

    args = parser.parse_args()

    # Priority: CLI arg > config.json > built-in default
    config = load_config()
    output_dir = args.output_dir or config.get("output_dir") or DEFAULT_OUTPUT_DIR
    result_dir = Path(args.result_dir or config.get("result_dir") or DEFAULT_RESULT_DIR)

    # Collect raw inputs from positional args and/or file
    raw_inputs = list(args.urls)
    if args.file:
        source = sys.stdin if args.file == "-" else open(args.file, encoding="utf-8")
        try:
            raw_inputs.extend(line.strip() for line in source if line.strip())
        finally:
            if args.file != "-":
                source.close()

    if not raw_inputs:
        parser.error("Provide at least one YouTube URL or video ID (or use --file).")

    # Parse and validate URLs
    urls = []
    for raw in raw_inputs:
        try:
            urls.append(parse_youtube_input(raw))
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    api_key = os.getenv("BRIGHTDATA_API_KEY")
    if not api_key:
        print(
            "Error: BRIGHTDATA_API_KEY is not set. Add it to your .env file or environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Determine output path before triggering so numbering is reserved early
    date_str = datetime.now().strftime("%Y-%m-%d")
    folder = Path(output_dir) / date_str
    folder.mkdir(parents=True, exist_ok=True)
    number = next_output_number(folder)
    output_path = folder / f"youtube_{number}.json"

    print(f"Triggering scrape for {len(urls)} URL(s):")
    for u in urls:
        print(f"  {u}")

    snapshot_id = trigger_scrape(api_key, urls)
    print(f"Snapshot ID: {snapshot_id}")
    print(f"Polling for results (timeout: {args.timeout}s, interval: {POLL_INTERVAL}s)...")

    try:
        poll_until_ready(api_key, snapshot_id, args.timeout)
    except TimeoutError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Downloading snapshot to {output_path} ...")
    download_snapshot(api_key, snapshot_id, output_path)
    print(f"Saved raw snapshot to {output_path}")

    print(f"Extracting results to {result_dir} ...")
    saved = extract_results(output_path, result_dir)
    for p in saved:
        print(f"  {p}")
    print(f"Done. {len(saved)} result file(s) written.")


if __name__ == "__main__":
    main()
