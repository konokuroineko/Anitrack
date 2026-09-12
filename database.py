import sqlite3

DATABASE_NAME = "anime_tracker.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, type TEXT NOT NULL,
            description TEXT, episodes INTEGER, score REAL, start_year INTEGER,
            cover_url TEXT, format TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_relations (
            source_id INTEGER NOT NULL, target_id INTEGER NOT NULL, relation_type TEXT NOT NULL,
            PRIMARY KEY (source_id, target_id, relation_type)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_library (
            work_id INTEGER PRIMARY KEY, status TEXT NOT NULL DEFAULT 'Planning',
            progress_episodes INTEGER DEFAULT 0, progress_chapters INTEGER DEFAULT 0,
            rating INTEGER, notes TEXT, added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (work_id) REFERENCES works(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, image_url TEXT, image_path TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, image_url TEXT, image_path TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_characters (
            work_id INTEGER NOT NULL, character_id INTEGER NOT NULL,
            PRIMARY KEY (work_id, character_id), FOREIGN KEY (work_id) REFERENCES works(id),
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_voice_actors (
            character_id INTEGER NOT NULL, person_id INTEGER NOT NULL, language TEXT,
            PRIMARY KEY (character_id, person_id), FOREIGN KEY (character_id) REFERENCES characters(id),
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_staff (
            work_id INTEGER NOT NULL, person_id INTEGER NOT NULL, role TEXT NOT NULL,
            PRIMARY KEY (work_id, person_id, role), FOREIGN KEY (work_id) REFERENCES works(id),
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)
    columns = cursor.execute("PRAGMA table_info(works)").fetchall()
    column_names = {column["name"] for column in columns}
    for column, definition in {
        "format": "TEXT", "cover_path": "TEXT", "chapters": "INTEGER", "volumes": "INTEGER",
        "source": "TEXT", "end_year": "INTEGER", "duration": "INTEGER",
    }.items():
        if column not in column_names:
            cursor.execute(f"ALTER TABLE works ADD COLUMN {column} {definition}")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alternate_titles (
            work_id INTEGER NOT NULL, title TEXT NOT NULL, language TEXT,
            PRIMARY KEY (work_id, title, language), FOREIGN KEY (work_id) REFERENCES works(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studios (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, is_main INTEGER NOT NULL DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_studios (
            work_id INTEGER NOT NULL, studio_id INTEGER NOT NULL,
            PRIMARY KEY (work_id, studio_id), FOREIGN KEY (work_id) REFERENCES works(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, work_id INTEGER NOT NULL,
            episode_number INTEGER NOT NULL, title TEXT, description TEXT, air_date TEXT,
            watched INTEGER NOT NULL DEFAULT 0, UNIQUE (work_id, episode_number),
            FOREIGN KEY (work_id) REFERENCES works(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL, artist TEXT, image_url TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_songs (
            work_id INTEGER NOT NULL, song_id INTEGER NOT NULL, song_type TEXT NOT NULL,
            song_number INTEGER, PRIMARY KEY (work_id, song_id, song_type),
            FOREIGN KEY (work_id) REFERENCES works(id), FOREIGN KEY (song_id) REFERENCES songs(id)
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
        connection.execute("INSERT OR REPLACE INTO characters (id, name, image_url) VALUES (?, ?, ?)",
                           (character_id, name, (character.get("image") or {}).get("large")))
        connection.execute("INSERT OR IGNORE INTO work_characters (work_id, character_id) VALUES (?, ?)",
                           (work_id, character_id))
        for actor in edge.get("voiceActors") or []:
            person_id = actor.get("id")
            person_name = actor.get("name") or {}
            if not person_id or not person_name.get("full"):
                continue
            connection.execute("INSERT OR REPLACE INTO people (id, name, image_url) VALUES (?, ?, ?)",
                               (person_id, person_name["full"], (actor.get("image") or {}).get("large")))
            connection.execute("""
                INSERT OR REPLACE INTO character_voice_actors (character_id, person_id, language)
                VALUES (?, ?, ?)
            """, (character_id, person_id, actor.get("language")))
    connection.commit()
    connection.close()


def get_characters(work_id):
    connection = get_connection()
    results = connection.execute("""
        SELECT characters.id, characters.name AS character_name,
               characters.image_path AS character_image_path, characters.image_url AS character_image_url,
               people.name AS person_name, people.image_path AS person_image_path,
               people.image_url AS person_image_url, character_voice_actors.language
        FROM work_characters JOIN characters ON characters.id = work_characters.character_id
        LEFT JOIN character_voice_actors ON character_voice_actors.character_id = characters.id
        LEFT JOIN people ON people.id = character_voice_actors.person_id
        WHERE work_characters.work_id = ? ORDER BY characters.name, character_voice_actors.language
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
        connection.execute("INSERT OR REPLACE INTO people (id, name, image_url) VALUES (?, ?, ?)",
                           (person_id, person_name, (person.get("image") or {}).get("large")))
        connection.execute("INSERT OR IGNORE INTO work_staff (work_id, person_id, role) VALUES (?, ?, ?)",
                           (work_id, person_id, role))
    connection.commit()
    connection.close()


def get_staff(work_id):
    connection = get_connection()
    results = connection.execute("""
        SELECT people.name, people.image_path, people.image_url, work_staff.role
        FROM work_staff JOIN people ON people.id = work_staff.person_id
        WHERE work_staff.work_id = ? ORDER BY work_staff.role, people.name
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
            INSERT INTO episodes (work_id, episode_number, title, description, air_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(work_id, episode_number) DO UPDATE SET
                title = excluded.title, description = excluded.description, air_date = excluded.air_date
        """, (work_id, number, episode.get("title"), episode.get("description"), episode.get("airdate")))
    connection.commit()
    connection.close()


def get_episodes(work_id):
    connection = get_connection()
    results = connection.execute("SELECT * FROM episodes WHERE work_id = ? ORDER BY episode_number", (work_id,)).fetchall()
    connection.close()
    return results


def set_episode_watched(work_id, episode_number, watched):
    connection = get_connection()
    connection.execute("UPDATE episodes SET watched = ? WHERE work_id = ? AND episode_number = ?",
                       (1 if watched else 0, work_id, episode_number))
    watched_count = connection.execute("SELECT COUNT(*) FROM episodes WHERE work_id = ? AND watched = 1", (work_id,)).fetchone()[0]
    total = connection.execute("SELECT COUNT(*) FROM episodes WHERE work_id = ?", (work_id,)).fetchone()[0]
    if connection.execute("SELECT 1 FROM user_library WHERE work_id = ?", (work_id,)).fetchone():
        status = "Completed" if total and watched_count >= total else "Watching" if watched_count else "Planning"
        connection.execute("""
            UPDATE user_library SET progress_episodes = ?, status = ?, updated_date = CURRENT_TIMESTAMP
            WHERE work_id = ?
        """, (watched_count, status, work_id))
    connection.commit()
    connection.close()
