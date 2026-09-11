# NekoTrack

A personal anime and media tracker built with Python, PySide6, SQLite, and the AniList GraphQL API.

NekoTrack is designed to keep your library, progress, metadata, relationships, characters, staff, and locally cached artwork in one desktop application.

> **Status: Beta — v0.1.0-beta.1**
>
> NekoTrack is usable, but it is still under active development. Expect unfinished features, UI changes, and occasional bugs while the beta is being developed.

## Features

- Search AniList
- Anime, manga, and novel search modes
- Local SQLite library
- Add works to your personal library
- Episode progress and watched-state tracking
- Local cover caching
- Work relationships and franchise connections
- Character and voice-actor data model
- Staff data model
- Studio data model
- Alternate titles
- Episode data model
- Song/music data model
- Work detail, character, person, and relationship pages
- Configurable dark desktop interface built with PySide6
- Library card sizing, spacing, hover, and resize animation preferences
- Maximized startup preference
- Scrollable settings page

## Known limitations

- AniList access is required for online search and metadata retrieval.
- Online features may be unavailable when the AniList service or API is unavailable.
- Windows packaging and an installer are not included yet; this beta is run from Python.
- Some planned media, tracking, metadata, and filtering features are still being developed.

## Planned

- More complete anime / manga / novel support
- Better franchise and relationship browsing
- More complete character, staff, and voice-actor pages
- Episode and chapter tracking improvements
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

## Updating

For an existing checkout on the `main` branch:

```powershell
git pull
```

Then run:

```powershell
python main.py
```

## Data and privacy

NekoTrack stores its local SQLite database as `anime_tracker.db`. Cover images are cached under `data/images/`. These generated/local files are intentionally ignored by Git.

NekoTrack does not currently require an AniList API token for its public GraphQL requests.

## AniList

NekoTrack uses the AniList GraphQL API for media metadata. AniList data, artwork, and trademarks remain subject to their respective terms and rights. This repository's MIT license applies to NekoTrack's own source code; it does not grant ownership of third-party AniList content.

See the AniList API documentation for current API and usage terms: https://anilist.gitbook.io/anilist-apiv2-docs/

## License

NekoTrack's source code is released under the MIT License. See [LICENSE](LICENSE).

## AI-assisted development

NekoTrack has been developed with assistance from AI coding tools, including GitHub Copilot and OpenAI ChatGPT. The project is still maintained and reviewed by its author.
