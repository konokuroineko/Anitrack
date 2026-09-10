import sqlite3


DATABASE_NAME = "anime_tracker.db"


def get_connection():

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # =========================
    # Works
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            episodes INTEGER,
            score REAL,
            start_year INTEGER,
            cover_url TEXT,
            format TEXT
        )
    """)

    # =========================
    # Relationships
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_relations (
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL,

            PRIMARY KEY (
                source_id,
                target_id,
                relation_type
            )
        )
    """)

    # =========================
    # User Library
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_library (
            work_id INTEGER PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'Planning',
            progress_episodes INTEGER DEFAULT 0,
            progress_chapters INTEGER DEFAULT 0,
            rating INTEGER,
            notes TEXT,
            added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (work_id) REFERENCES works(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            image_url TEXT,
            image_path TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            image_url TEXT,
            image_path TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_characters (
            work_id INTEGER NOT NULL,
            character_id INTEGER NOT NULL,
            PRIMARY KEY (work_id, character_id),
            FOREIGN KEY (work_id) REFERENCES works(id),
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_voice_actors (
            character_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            language TEXT,
            PRIMARY KEY (character_id, person_id),
            FOREIGN KEY (character_id) REFERENCES characters(id),
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_staff (
            work_id INTEGER NOT NULL,
            person_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            PRIMARY KEY (work_id, person_id, role),
            FOREIGN KEY (work_id) REFERENCES works(id),
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)

    # =========================
    # Database migration
    # =========================

    columns = cursor.execute(
        "PRAGMA table_info(works)"
    ).fetchall()

    column_names = {
        column["name"]
        for column in columns
    }

    if "format" not in column_names:
        cursor.execute("ALTER TABLE works ADD COLUMN format TEXT")

    if "cover_path" not in column_names:
        cursor.execute("ALTER TABLE works ADD COLUMN cover_path TEXT")

    for column, definition in {
        "chapters": "INTEGER",
        "volumes": "INTEGER",
        "source": "TEXT",
        "end_year": "INTEGER",
        "duration": "INTEGER",
    }.items():
        if column not in column_names:
            cursor.execute(f"ALTER TABLE works ADD COLUMN {column} {definition}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alternate_titles (
            work_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            language TEXT,
            PRIMARY KEY (work_id, title, language),
            FOREIGN KEY (work_id) REFERENCES works(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studios (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            is_main INTEGER NOT NULL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_studios (
            work_id INTEGER NOT NULL,
            studio_id INTEGER NOT NULL,
            PRIMARY KEY (work_id, studio_id),
            FOREIGN KEY (work_id) REFERENCES works(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id INTEGER NOT NULL,
            episode_number INTEGER NOT NULL,
            title TEXT,
            description TEXT,
            air_date TEXT,
            watched INTEGER NOT NULL DEFAULT 0,
            UNIQUE (work_id, episode_number),
            FOREIGN KEY (work_id) REFERENCES works(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            artist TEXT,
            image_url TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_songs (
            work_id INTEGER NOT NULL,
            song_id INTEGER NOT NULL,
            song_type TEXT NOT NULL,
            song_number INTEGER,
            PRIMARY KEY (work_id, song_id, song_type),
            FOREIGN KEY (work_id) REFERENCES works(id),
            FOREIGN KEY (song_id) REFERENCES songs(id)
        )
    """)

    connection.commit()
    connection.close()


def save_characters(work_id, characters):
    connection = get_connection()
    for edge in characters or []:
        character = edge.get("node") or {}
        character_id = character.get("id")
        name = (character.get("name") or {}).get("full")
        if not character_id or not name:
            continue
        image_url = (character.get("image") or {}).get("large")
        connection.execute("""
            INSERT OR REPLACE INTO characters (id, name, image_url)
            VALUES (?, ?, ?)
        """, (character_id, name, image_url))
        connection.execute("""
            INSERT OR IGNORE INTO work_characters (work_id, character_id)
            VALUES (?, ?)
        """, (work_id, character_id))
        for actor in character.get("voiceActors") or []:
            person_id = actor.get("id")
            person_name = actor.get("name") or {}
            if not person_id or not person_name.get("full"):
                continue
            actor_image = (actor.get("image") or {}).get("large")
            connection.execute("""
                INSERT OR REPLACE INTO people (id, name, image_url)
                VALUES (?, ?, ?)
            """, (person_id, person_name["full"], actor_image))
            connection.execute("""
                INSERT OR REPLACE INTO character_voice_actors
                    (character_id, person_id, language)
                VALUES (?, ?, ?)
            """, (character_id, person_id, actor.get("language")))
    connection.commit()
    connection.close()


def get_characters(work_id):
    connection = get_connection()
    results = connection.execute("""
        SELECT
            characters.id,
            characters.name AS character_name,
            characters.image_path AS character_image_path,
            characters.image_url AS character_image_url,
            people.name AS person_name,
            people.image_path AS person_image_path,
            people.image_url AS person_image_url,
            character_voice_actors.language
        FROM work_characters
        JOIN characters ON characters.id = work_characters.character_id
        LEFT JOIN character_voice_actors
            ON character_voice_actors.character_id = characters.id
        LEFT JOIN people ON people.id = character_voice_actors.person_id
        WHERE work_characters.work_id = ?
        ORDER BY characters.name, character_voice_actors.language
    """, (work_id,)).fetchall()
    connection.close()
    return results


def save_staff(work_id, staff_edges):
    connection = get_connection()
    for edge in staff_edges or []:
        person = edge.get("node") or {}
        person_id = person.get("id")
        person_name = (person.get("name") or {}).get("full")
        role = edge.get("role")
        if not person_id or not person_name or not role:
            continue
        image_url = (person.get("image") or {}).get("large")
        connection.execute("""
            INSERT OR REPLACE INTO people (id, name, image_url)
            VALUES (?, ?, ?)
        """, (person_id, person_name, image_url))
        connection.execute("""
            INSERT OR IGNORE INTO work_staff (work_id, person_id, role)
            VALUES (?, ?, ?)
        """, (work_id, person_id, role))
    connection.commit()
    connection.close()


def get_staff(work_id):
    connection = get_connection()
    results = connection.execute("""
        SELECT people.name, people.image_path, people.image_url, work_staff.role
        FROM work_staff
        JOIN people ON people.id = work_staff.person_id
        WHERE work_staff.work_id = ?
        ORDER BY work_staff.role, people.name
    """, (work_id,)).fetchall()
    connection.close()
    return results


def save_episodes(work_id, episode_data):
    connection = get_connection()
    for episode in episode_data or []:
        number = episode.get("episodeNumber")
        if number is None:
            continue
        connection.execute("""
            INSERT INTO episodes
                (work_id, episode_number, title, description, air_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(work_id, episode_number) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                air_date = excluded.air_date
        """, (
            work_id,
            number,
            episode.get("title"),
            episode.get("description"),
            episode.get("airdate")
        ))
    connection.commit()
    connection.close()


def get_episodes(work_id):
    connection = get_connection()
    results = connection.execute("""
        SELECT * FROM episodes
        WHERE work_id = ?
        ORDER BY episode_number
    """, (work_id,)).fetchall()
    connection.close()
    return results


def save_anime(anime):
    title_data = anime["title"]
    title = (
        title_data.get("english")
        or title_data.get("romaji")
        or title_data.get("native")
    )
    start_year = (anime.get("startDate") or {}).get("year")
    cover_image = anime.get("coverImage") or {}
    connection = get_connection()

    connection.execute("""
        INSERT INTO works (
            id, title, type, description, episodes, score, start_year,
            cover_url, format, chapters, volumes, source, end_year, duration
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            type = excluded.type,
            description = excluded.description,
            episodes = excluded.episodes,
            score = excluded.score,
            start_year = excluded.start_year,
            cover_url = excluded.cover_url,
            format = excluded.format,
            chapters = excluded.chapters,
            volumes = excluded.volumes,
            source = excluded.source,
            end_year = excluded.end_year,
            duration = excluded.duration
    """, (
        anime["id"], title, anime.get("type") or "ANIME",
        anime.get("description"), anime.get("episodes"), anime.get("averageScore"),
        start_year, cover_image.get("large"), anime.get("format"),
        anime.get("chapters"), anime.get("volumes"), anime.get("source"),
        (anime.get("endDate") or {}).get("year"), anime.get("duration")
    ))

    for synonym in anime.get("synonyms") or []:
        connection.execute("""
            INSERT OR IGNORE INTO alternate_titles (work_id, title, language)
            VALUES (?, ?, ?)
        """, (anime["id"], synonym, None))

    for edge in (anime.get("studios") or {}).get("edges") or []:
        studio = edge.get("node") or {}
        studio_id = studio.get("id")
        studio_name = studio.get("name")
        if not studio_id or not studio_name:
            continue
        connection.execute("""
            INSERT OR REPLACE INTO studios (id, name, is_main)
            VALUES (?, ?, ?)
        """, (studio_id, studio_name, 1 if edge.get("isMain") else 0))
        connection.execute("""
            INSERT OR IGNORE INTO work_studios (work_id, studio_id)
            VALUES (?, ?)
        """, (anime["id"], studio_id))

    relations = anime.get("relations") or {}
    for edge in relations.get("edges") or []:
        relation_type = edge.get("relationType")
        node = edge.get("node")
        if not node:
            continue
        target_id = node.get("id")
        if not target_id:
            continue
        target_title_data = node.get("title") or {}
        target_title = (
            target_title_data.get("english")
            or target_title_data.get("romaji")
            or target_title_data.get("native")
        )
        if target_title:
            target_cover = node.get("coverImage") or {}
            connection.execute("""
                INSERT OR IGNORE INTO works
                    (id, title, type, format, cover_url)
                VALUES (?, ?, ?, ?, ?)
            """, (
                target_id, target_title, node.get("type") or "ANIME",
                node.get("format"), target_cover.get("large")
            ))
        connection.execute("""
            INSERT OR REPLACE INTO work_relations
                (source_id, target_id, relation_type)
            VALUES (?, ?, ?)
        """, (anime["id"], target_id, relation_type))

    connection.commit()
    connection.close()


def save_cover_path(work_id, cover_path):
    connection = get_connection()
    connection.execute(
        "UPDATE works SET cover_path = ? WHERE id = ?",
        (cover_path, work_id)
    )
    connection.commit()
    connection.close()


def get_saved_anime():
    connection = get_connection()
    results = connection.execute(
        "SELECT * FROM works ORDER BY title"
    ).fetchall()
    connection.close()
    return results


def get_work(work_id):
    connection = get_connection()
    result = connection.execute(
        "SELECT * FROM works WHERE id = ?",
        (work_id,)
    ).fetchone()
    connection.close()
    return result


def get_relations(work_id):
    connection = get_connection()
    results = connection.execute("""
        SELECT
            work_relations.*,
            works.title,
            works.format,
            works.type,
            works.cover_url,
            works.cover_path
        FROM work_relations
        LEFT JOIN works ON works.id = work_relations.target_id
        WHERE work_relations.source_id = ?
        ORDER BY relation_type, title
    """, (work_id,)).fetchall()
    connection.close()
    return results


# =========================
# User Library Functions
# =========================

def add_to_library(work_id, status="Planning"):
    connection = get_connection()
    connection.execute("""
        INSERT OR REPLACE INTO user_library
            (work_id, status, progress_episodes, updated_date)
        VALUES (?, ?, 0, CURRENT_TIMESTAMP)
    """, (work_id, status))
    connection.commit()
    connection.close()


def get_library_by_status(status):
    connection = get_connection()
    results = connection.execute("""
        SELECT
            works.*,
            user_library.status,
            user_library.progress_episodes,
            user_library.progress_chapters,
            user_library.rating,
            user_library.notes
        FROM user_library
        JOIN works ON works.id = user_library.work_id
        WHERE user_library.status = ?
        ORDER BY works.title
    """, (status,)).fetchall()
    connection.close()
    return results


def get_all_library():
    connection = get_connection()
    results = connection.execute("""
        SELECT
            works.*,
            user_library.status,
            user_library.progress_episodes,
            user_library.progress_chapters,
            user_library.rating,
            user_library.notes
        FROM user_library
        JOIN works ON works.id = user_library.work_id
        ORDER BY works.title
    """).fetchall()
    connection.close()
    return results


def update_library_progress(work_id, episodes=None, chapters=None):
    connection = get_connection()
    if episodes is not None:
        connection.execute("""
            UPDATE user_library
            SET progress_episodes = ?, updated_date = CURRENT_TIMESTAMP
            WHERE work_id = ?
        """, (episodes, work_id))
    if chapters is not None:
        connection.execute("""
            UPDATE user_library
            SET progress_chapters = ?, updated_date = CURRENT_TIMESTAMP
            WHERE work_id = ?
        """, (chapters, work_id))
    connection.commit()
    connection.close()
