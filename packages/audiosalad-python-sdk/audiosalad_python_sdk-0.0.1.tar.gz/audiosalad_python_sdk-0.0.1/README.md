# mtl-audiosalad-sdk

Unofficial, experimental Python SDK for interacting with AudioSalad APIs.

It provides three layers:

- `services/audiosalad_client.py` — low-level HTTP client for AudioSalad client API
- `services/audiosalad_api.py` — higher-level service wrapper with safe defaults and logging
- `services/audiosalad_web.py` — web layer for endpoints that require browser-like headers/cookies

## Status

- Experimental and subject to change
- Not affiliated with AudioSalad

## Installation

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) (or use your preferred tooling)

### Install

```bash
git clone https://github.com/musictechlab/mtl-audiosalad-sdk.git
cd mtl-audiosalad-sdk
poetry install
```

## Configuration

Set the following environment variables (recommended):

- `AUDIOSALAD_ACCESS_ID` — your AudioSalad access ID
- `AUDIOSALAD_REFRESH_TOKEN` — your AudioSalad refresh token
- `AUDIOSALAD_API_URL` — base URL (defaults to `https://<client-namespace>.dashboard.audiosalad.com`)
- `AUDIOSALAD_TOKEN_FILE` — path to persist tokens (defaults to `/tmp/audiosalad_tokens.json`)

Example:

```bash
export AUDIOSALAD_ACCESS_ID=xxx
export AUDIOSALAD_REFRESH_TOKEN=yyy
# optional overrides
export AUDIOSALAD_API_URL=https://<client-namespace>.dashboard.audiosalad.com
export AUDIOSALAD_TOKEN_FILE=/tmp/audiosalad_tokens.json
```

## Quickstart

### Low-level client (`AudioSaladClient`)

```python
from services.audiosalad_client import AudioSaladClient

client = AudioSaladClient(
    # If omitted, values are read from environment variables
    access_id="your_access_id",
    refresh_token="your_refresh_token",
    # base_url is optional; defaults to AUDIOSALAD_API_URL
)

# Releases
releases = client.get_releases(params={"page": 1, "page_length": 25})
release = client.get_release("release_id")

# Tracks
tracks = client.get_tracks(params={"page": 1})
track = client.get_track("track_id")

# Artists
artists = client.get_artists(params={"page": 1})
artist = client.get_artist("artist_id")

# Labels
labels = client.get_labels(params={"page": 1})
label_by_id = client.get_label(label_id=123)
label_by_name = client.get_label(label_name="My Label")

# Reports
sales = client.get_sales_report(start_date="2025-01-01", end_date="2025-01-31")
earnings = client.get_earnings_report(start_date="2025-01-01", end_date="2025-01-31")

# Ingestion (Dashboard/analytics endpoints)
ingestion = client.run_ingestion(
    label_id="123",
    s3_bucket="example-bucket.s3.us-east-1.amazonaws.com",
    s3_id="AWS_ACCESS_ID",
    s3_key="AWS_SECRET_KEY",
    s3_path="optional/prefix",
    wav_ready=10,
)
status = client.get_ingestion_status(ingest_id=ingestion.get("ingest_id", 0))

# Delivery
delivery = client.schedule_delivery(
    release_ids=["r1", "r2"],
    target_ids=["t1"],
    run_date="2025-01-31T10:00:00Z",
    action="full-update",
)
targets = client.list_delivery_targets()
delivery_status = client.get_delivery_status(release_ids=["r1"]) 
```

### High-level service (`AudioSaladAPI`)

```python
from services.audiosalad_api import AudioSaladAPI

service = AudioSaladAPI(
    access_id="your_access_id",
    refresh_token="your_refresh_token",
)

all_releases = service.get_all_releases(params={"page": 1})
release = service.get_release_by_id("release_id")

all_tracks = service.get_all_tracks(params={"page": 1})
track = service.get_track_by_id("track_id")

all_artists = service.get_all_artists(params={"page": 1})
artist = service.get_artist_by_id("artist_id")

all_labels = service.get_all_labels()
label = service.get_label_by_id(label_id=123)
label2 = service.get_label_by_name("My Label")

sales = service.get_sales_report_for_period()
earnings = service.get_earnings_report_for_period()

# Ingestion helpers
ing = service.run_ingestion(
    label_id="123",
    s3_bucket="example-bucket.s3.us-east-1.amazonaws.com",
    s3_id="AWS_ACCESS_ID",
    s3_key="AWS_SECRET_KEY",
)
ing_status = service.get_ingestion_status(ingest_id=ing.get("ingest_id", 0))

# Delivery helpers
targets = service.list_delivery_targets()
delivery = service.schedule_delivery(["r1"], ["t1"], "2025-01-31T10:00:00Z", "meta-update")
status = service.get_delivery_status(release_ids=["r1"]) 
```

### Web endpoints (`AudioSaladWebService`)

Some endpoints in the AudioSalad web app require browser-like headers and a valid `x-auth-token`. This helper wraps those flows.

```python
from services.audiosalad_web import AudioSaladWebService

web = AudioSaladWebService(auth_token="your_x_auth_token")

# Artists (auto-paginated)
artists = web.get_artists(page=1, page_length=50)

# Labels (single payload; API returns all labels)
labels = web.get_labels()

# Genres
genres = web.get_genres()
genre = web.get_genre("genre_id")
```

How to obtain `x-auth-token`:

1. Log in to the AudioSalad web interface: `https://<client-namespace>.audiosalad.com`
2. Open browser developer tools
3. Go to the Network tab, select any API request
4. Copy the `x-auth-token` header value
5. Use it to initialize `AudioSaladWebService`

Optionally, pass `cookie_token` if required by your environment.

## Examples

See `services/` for available methods. You can adapt the snippets above into runnable scripts.

## Tests

```bash
poetry run pytest
```

## Code quality

```bash
poetry run black .
poetry run autopep8 --in-place --recursive .
poetry run flake8
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feat/xyz`)
3. Make your changes
4. Ensure tests pass
5. Open a Pull Request

## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

MusicTechLab — Digital Commerce Solutions for the Music Industry

- Website: [musictechlab.io](https://www.musictechlab.io/)
- LinkedIn: [linkedin.com/company/musictechlab.io](https://linkedin.com/company/musictechlab.io)
- Contact: [office@musictechlab.io](mailto:office@musictechlab.io)
- Crafted by: [musictechlab.io](https://www.musictechlab.io/)
