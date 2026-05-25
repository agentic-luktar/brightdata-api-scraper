# Agent Instructions: brightdata-api-scraper

This tool downloads YouTube video data (including transcripts) via the Brightdata API and saves extracted results as JSON files.

The program is located at `~/dev/brightdata-api-scraper/` on this VPS.

## Setup (first time only)

```bash
cd ~/dev/brightdata-api-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

Activate the virtual environment first, then run with one or more YouTube video IDs or URLs:

```bash
cd ~/dev/brightdata-api-scraper
source venv/bin/activate
python -m scraper <youtube_id_1> <youtube_id_2>
```

Example:

```bash
python -m scraper EJYaiqV-pvs b6tPIquUMSA
```

## Output

Extracted results are saved to:

```
~/dev/brightdata-api-scraper/Result/<YYYY-MM-DD>/<video_id>.json
```

`<YYYY-MM-DD>` is a today's date

One file per video. Each file contains: `url`, `title`, `youtuber`, `handle_name`, and `transcript`.