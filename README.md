# brightdata-api-scraper

CLI tool that downloads YouTube video data via the [Brightdata](https://brightdata.com) scraping API and saves the results as JSON files.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set your BRIGHTDATA_API_KEY
```

## Usage

```
python -m scraper [URL_OR_ID ...] [--file FILE] [--timeout SECONDS] [--output-dir DIR]
```

Input can be YouTube watch URLs or bare video IDs, mixed freely:

```bash
# Bare video IDs
python -m scraper EJYaiqV-pvs b6tPIquUMSA

# Full watch URLs
python -m scraper https://www.youtube.com/watch?v=EJYaiqV-pvs

# Short URLs
python -m scraper https://youtu.be/EJYaiqV-pvs

# From a file (one URL or ID per line)
python -m scraper --file urls.txt

# From stdin
cat urls.txt | python -m scraper --file -

# Mix positional args and a file
python -m scraper EJYaiqV-pvs --file more_urls.txt
```

## Options

| Option | Default | Description |
|---|---|---|
| `URL_OR_ID` | — | One or more YouTube URLs or bare video IDs |
| `--file FILE`, `-f FILE` | — | File with one URL/ID per line; `-` reads from stdin |
| `--timeout SECONDS` | `600` | Max seconds to wait for Brightdata to return data |
| `--output-dir DIR` | `./Downloads` | Base directory for output files |
| `--help`, `-h` | — | Show help and exit |

## Output

Results are saved to:

```
Downloads/<YYYY-MM-DD>/youtube_<n>.json
```

The `Downloads/` folder is created inside the project directory and is git-ignored. Override it with `--output-dir`.

The number `<n>` starts at `1` and auto-increments, so running the script multiple times on the same day never overwrites previous results.

## How it works

1. Sends the list of YouTube URLs to the Brightdata trigger endpoint.
2. Receives a `snapshot_id` and polls the progress endpoint every 10 seconds.
3. Once the snapshot is `ready`, downloads the JSON result and saves it to the output file.
4. Exits with a non-zero status on timeout or API errors.
