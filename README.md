# AniTrack

A personal anime and media tracker built with Python, PySide6, SQLite, and the AniList GraphQL API.

AniTrack is designed to keep your library, progress, metadata, relationships, characters, staff, and locally cached artwork in one desktop application.

> **Status:** Early development. The project is usable, but several planned media types and tracking features are still being built.

## Features

- Search AniList
- Local SQLite library
- Add works to your personal library
- Episode progress tracking
- Local cover caching
- Work relationships
- Character and voice-actor data model
- Staff data model
- Studio data model
- Alternate titles
- Episode data model
- Song/music data model
- Dark desktop interface built with PySide6

## Planned

- Full anime / manga / novel support
- Better franchise and relationship browsing
- Complete character, staff, and voice-actor pages
- Episode and chapter tracking
- Library status filters
- Ratings, notes, and dates
- Improved search and filtering
- Better offline behavior
- Windows packaging and releases

## Requirements

- Python 3.10+
- Internet connection for AniList searches and metadata
- PySide6
- requests
- urllib3

## Installation

Clone the repository, create a virtual environment, install the dependencies, and run `main.py`.

```bash
git clone https://github.com/konokuroineko/Anitrack.git
cd Anitrack
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python main.py
```

If PowerShell blocks activation, you can run the environment's Python directly:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

## Data and privacy

AniTrack stores its local SQLite database as `anime_tracker.db`. Cover images are cached under `data/images/`. These generated/local files are intentionally ignored by Git.

AniTrack does not currently require an AniList API token for its public GraphQL requests.

## AniList

AniTrack uses the AniList GraphQL API for media metadata. AniList data, artwork, and trademarks remain subject to their respective terms and rights. This repository's MIT license applies to AniTrack's own source code; it does not grant ownership of third-party AniList content.

See the AniList API documentation for current API and usage terms: https://anilist.gitbook.io/anilist-apiv2-docs/

## License

AniTrack's source code is released under the MIT License. See [LICENSE](LICENSE).

## AI-assisted development

AniTrack has been developed with assistance from AI coding tools, including GitHub Copilot and OpenAI ChatGPT. The project is still maintained and reviewed by its author.
