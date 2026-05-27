# Agent Instructions: brightdata-api-scraper

This tool downloads YouTube video data (including transcripts) via the Brightdata API and saves extracted results as JSON files.

The program is located at `~/dev/brightdata-api-scraper/` on this VPS.

## Running

Use `scraper.sh` — it automatically creates the venv, installs requirements when the version changes, and forwards all arguments to the scraper:

```bash
cd ~/dev/brightdata-api-scraper
./scraper.sh <youtube_id_1> <youtube_id_2>
```

Example:

```bash
./scraper.sh EJYaiqV-pvs b6tPIquUMSA
```

All flags are forwarded to the Python script:

```bash
./scraper.sh --file urls.txt --timeout 600
./scraper.sh https://www.youtube.com/watch?v=EJYaiqV-pvs --result-dir /tmp/results
```

## Output

Extracted results are saved to:

```
~/dev/brightdata-api-scraper/Result/<YYYY-MM-DD>/<video_id>.json
```

`<YYYY-MM-DD>` is today's date.

One file per video. Each file contains: `url`, `title`, `youtuber`, `handle_name`, and `transcript`.
