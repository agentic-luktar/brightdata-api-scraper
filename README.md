# brightdata-api-scraper

CLI tool that downloads YouTube video data via the [Brightdata](https://brightdata.com) scraping API and saves the results as JSON files.

## Setup

```bash
cp .env.example .env
# Edit .env and set your BRIGHTDATA_API_KEY
```

## Usage

Use `scraper.sh` — it handles venv creation, dependency installation, and argument forwarding automatically:

```bash
./scraper.sh [URL_OR_ID ...] [--file FILE] [--timeout SECONDS] [--output-dir DIR] [--result-dir DIR]
```

Dependencies are only reinstalled when the version in `scraper/__init__.py` changes.

### Examples

```bash
# Bare video IDs
./scraper.sh EJYaiqV-pvs b6tPIquUMSA

# Full watch URLs
./scraper.sh https://www.youtube.com/watch?v=EJYaiqV-pvs

# Short URLs
./scraper.sh https://youtu.be/EJYaiqV-pvs

# From a file (one URL or ID per line)
./scraper.sh --file urls.txt

# From stdin
cat urls.txt | ./scraper.sh --file -

# Mix positional args and a file
./scraper.sh EJYaiqV-pvs --file more_urls.txt
```

## Options

| Option | Default | Description |
|---|---|---|
| `URL_OR_ID` | — | One or more YouTube URLs or bare video IDs |
| `--file FILE`, `-f FILE` | — | File with one URL/ID per line; `-` reads from stdin |
| `--timeout SECONDS` | `600` | Max seconds to wait for Brightdata to return data |
| `--output-dir DIR` | `./Downloads` | Base directory for raw snapshot files |
| `--result-dir DIR` | `./Result` | Base directory for extracted result files |
| `--help`, `-h` | — | Show help and exit |

## Output

Raw snapshots are saved to:

```
Downloads/<YYYY-MM-DD>/youtube_<n>.json
```

Extracted results (one file per video) are saved to:

```
Result/<YYYY-MM-DD>/<video_id>.json
```

Each result file contains: `url`, `title`, `youtuber`, `handle_name`, `transcript`.

The number `<n>` auto-increments so parallel invocations never overwrite each other. Both directories are git-ignored and can be overridden via flags or `config.json`.

## How it works

1. Sends the list of YouTube URLs to the Brightdata trigger endpoint.
2. Receives a `snapshot_id` and polls the progress endpoint every 10 seconds.
3. Once the snapshot is `ready`, downloads the raw JSON and saves it under `Downloads/`.
4. Extracts slim per-video JSON files into `Result/`.
5. Exits with a non-zero status on timeout or API errors.
