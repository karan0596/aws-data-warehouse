import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES

staging_events_table_create= ("""
    CREATE TABLE IF NOT EXISTS staging_events (
        artist          VARCHAR(500),
        auth            VARCHAR,
        firstName       VARCHAR,
        gender          VARCHAR,
        itemInSession   INTEGER,
        lastName        VARCHAR,
        length          NUMERIC,
        level           VARCHAR,
        location        VARCHAR,
        method          VARCHAR,
        page            VARCHAR,
        registration    BIGINT,
        sessionId       INTEGER,
        song            VARCHAR(500),
        status          INTEGER,
        ts              BIGINT,
        userAgent       VARCHAR,
        userId          INTEGER
     )
""")

staging_songs_table_create = ("""
    CREATE TABLE IF NOT EXISTS staging_songs (
        num_songs        INTEGER,
        artist_id        VARCHAR(255),
        artist_latitude  NUMERIC,
        artist_longitude NUMERIC,
        artist_location  VARCHAR(500),
        artist_name      VARCHAR(500),
        song_id          VARCHAR(255),
        title            VARCHAR(500),
        duration         NUMERIC,
        year             INTEGER
     )
""")

songplay_table_create = ("""
    CREATE TABLE IF NOT EXISTS songplays (
        songplay_id     VARCHAR,
        start_time      TIMESTAMP,
        user_id         INTEGER,
        level           VARCHAR,
        song_id         VARCHAR(255),
        artist_id       VARCHAR(255),
        session_id      INTEGER,
        location        VARCHAR,
        useragent       VARCHAR 
    )
""")

user_table_create = ("""
    CREATE TABLE IF NOT EXISTS users (
        user_id        INTEGER,
        first_name     VARCHAR,
        last_name      VARCHAR,
        gender         VARCHAR,
        level          VARCHAR
    )
""")

song_table_create = ("""
    CREATE TABLE IF NOT EXISTS songs (
        song_id        VARCHAR(255),
        title          VARCHAR(500),
        artist_id      VARCHAR(255),
        year           INTEGER,
        duration       NUMERIC
    )
""")

artist_table_create = ("""
    CREATE TABLE IF NOT EXISTS artists (
        artist_id      VARCHAR(255),
        name           VARCHAR(500),
        location       VARCHAR(500),
        latitude       NUMERIC,
        longitude      NUMERIC
    )
""")

time_table_create = ("""
    CREATE TABLE IF NOT EXISTS time (
        start_time    TIMESTAMP,
        hour          INTEGER,
        day           INTEGER,
        week          INTEGER,
        month         INTEGER,
        year          INTEGER,
        weekday       INTEGER
    )
""")

# STAGING TABLES

staging_events_copy = ("""
    COPY {table}
    FROM {s3_path}
    IAM_ROLE {iam_role}
    FORMAT AS JSON {json_path}
    REGION {region}
""").format(
    table='staging_events',
    s3_path=config.get('S3', 'LOG_DATA'),
    iam_role=config.get('IAM_ROLE', 'ARN'),
    json_path=config.get('S3', 'LOG_JSONPATH'),
    region=config.get('S3', 'REGION') 
)

staging_songs_copy = ("""
    COPY {table}
    FROM {s3_path}
    IAM_ROLE {iam_role}
    FORMAT AS JSON '{json_path}'
    REGION {region}
""").format(
    table='staging_songs',
    s3_path=config.get('S3', 'SONG_DATA'),
    iam_role=config.get('IAM_ROLE', 'ARN'),
    json_path='auto',
    region=config.get('S3', 'REGION') 
)

# FINAL TABLES

songplay_table_insert = ("""
    INSERT INTO songplays 
        SELECT  md5(events.sessionid || events.start_time) songplay_id,
        events.start_time, 
        events.userId, 
        events.level, 
        songs.song_id, 
        songs.artist_id, 
        events.sessionId, 
        events.location, 
        events.useragent
    FROM (SELECT TIMESTAMP 'epoch' + ts/1000 * interval '1 second' AS start_time, *
        FROM staging_events
        WHERE page='NextSong') events
    LEFT JOIN staging_songs songs
    ON events.song = songs.title
        AND events.artist = songs.artist_name
""")

user_table_insert = ("""
    INSERT INTO users
    SELECT distinct userId, firstName, lastName, gender, level
    FROM staging_events
    WHERE page='NextSong'
""")

song_table_insert = ("""
    INSERT INTO songs
    SELECT distinct song_id, title, artist_id, year, duration
    FROM staging_songs
""")

artist_table_insert = ("""
    INSERT INTO artists
    SELECT distinct artist_id, artist_name, artist_location, artist_latitude, artist_longitude
    FROM staging_songs
""")

time_table_insert = ("""
    INSERT INTO time
    SELECT start_time, extract(hour from start_time), extract(day from start_time), 
    extract(week from start_time), extract(month from start_time), 
    extract(year from start_time), extract(weekday from start_time)
    FROM songplays
""")



# =========================
# ANALYTICS QUERIES
# =========================

most_played_song_query = """
SELECT
    songplays.song_id,
    songs.title,
    COUNT(*) AS songs_played
FROM songplays
JOIN songs
    ON songs.song_id = songplays.song_id
WHERE songplays.song_id IS NOT NULL
GROUP BY songplays.song_id, songs.title
ORDER BY songs_played DESC
LIMIT 1;
"""

peak_hour_query = """
SELECT
    EXTRACT(hour FROM start_time) AS hour,
    COUNT(songplay_id) AS total_plays
FROM songplays
GROUP BY hour
ORDER BY total_plays DESC
LIMIT 1;
"""

regional_behavior_query = """
SELECT
    location,
    COUNT(DISTINCT user_id) AS active_users,
    COUNT(*) AS total_plays,
    COUNT(*) * 1.0 / COUNT(DISTINCT user_id) AS avg_plays_per_user
FROM songplays
GROUP BY location
ORDER BY total_plays DESC
LIMIT 5;
"""

user_level_session_query = """
SELECT
    level,
    COUNT(*) * 1.0 / COUNT(DISTINCT session_id) AS avg_plays_per_session
FROM songplays
GROUP BY level;
"""

return_time_query = """
WITH user_start_session AS (
    SELECT
        user_id,
        session_id,
        MIN(start_time) AS session_start
    FROM songplays
    GROUP BY user_id, session_id
),
session_gaps AS (
    SELECT
        user_id,
        session_start,
        session_start - LAG(session_start) OVER (
            PARTITION BY user_id
            ORDER BY session_start
        ) AS session_time_diff
    FROM user_start_session
)
SELECT
    ROUND(
        AVG(EXTRACT(EPOCH FROM session_time_diff)) / 86400.0,
        2
    ) AS gap_in_days
FROM session_gaps
WHERE session_time_diff IS NOT NULL;
"""







# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
