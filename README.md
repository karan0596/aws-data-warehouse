# 🎧 Sparkify Data Warehouse (AWS Redshift ETL Pipeline)

## 📌 Project Overview

Sparkify, a growing music streaming startup, wants to transition its data infrastructure to the cloud to support scalable analytics. Their data currently resides in JSON logs stored in Amazon S3, containing:

- User activity logs from the music streaming app
- Song metadata from the Million Song Dataset

The goal of this project is to build an ETL pipeline that extracts data from S3, stages it in Amazon Redshift, and transforms it into a star schema optimized for analytical queries.

This enables Sparkify’s analytics team to efficiently analyze user behavior, song popularity, and listening trends.

## 🚀 How to Run

### 1️⃣ Clone repository
```
git clone <repo-url>
cd <repo-name>
```

### 2️⃣ Configure credentials

Update dwh.cfg:
```
[CLUSTER]
HOST=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_PORT=

[IAM_ROLE]
ARN=

[S3]
LOG_DATA=
LOG_JSONPATH=
SONG_DATA=
REGION=
```

### 3️⃣ Create tables
```
python create_tables.py
```

### 4️⃣ Run ETL pipeline & analytics report
```
python etl.py
```

## 📁 Project Structure
```
├── create_tables.py      # Schema creation (DDL)
├── etl.py                # ETL pipeline (Staging → Warehouse)
├── sql_queries.py        # Centralized SQL repository 
├── dwh.cfg               # Configuration file (excluded from Git)
├── README.md

```

## ❓ Project Discussion Question

### Question

**1. Discuss the purpose of this database in the context of the startup, Sparkify, and their analytical goals.**

#### Answer

The purpose of this database is to support Sparkify’s transition from a file-based storage system (JSON logs in S3) to a scalable cloud data warehouse using Amazon Redshift.

As Sparkify’s user base and song catalog grow, querying raw JSON files becomes inefficient and does not support complex analytical queries. This data warehouse solves that problem by:

- Centralizing data from multiple sources (user activity logs and song metadata)
- Structuring raw data into analytics-ready tables using a star schema
- Enabling fast, scalable SQL queries for business intelligence

The database allows Sparkify to transform raw event data into meaningful insights that support decision-making and product growth.

---

### Question
**2. State and justify your database schema design and ETL pipeline**

#### Answer
The database is designed using a **Star Schema architecture**, optimized for analytical queries on music streaming behavior in Sparkify. This design consists of one central fact table (`songplays`) surrounded by four dimension tables (`users`, `songs`, `artists`, `time`).

#### ⭐ Why Star Schema?

A star schema was chosen because it:

- Simplifies complex analytical queries by reducing the number of joins
- Improves query performance in Redshift through a denormalized structure
- Is optimized for OLAP (Online Analytical Processing) workloads
- Supports fast aggregation for business insights such as user behavior and song popularity

---

#### 📌 Fact Table: `songplays`

The `songplays` table is the core of the schema and stores **event-level data** for each song play action (`page = 'NextSong'`).

It includes:

- user activity (user_id, session_id, level)
- song metadata references (song_id, artist_id)
- contextual information (location, user_agent, start_time)

#### 📚 Dimension Tables

#### 👤 users
Stores user profile information:
- Enables analysis of user demographics and subscription levels

#### 🎵 songs
Stores song metadata:
- Enables analysis of song popularity and catalog structure

#### 🎤 artists
Stores artist metadata:
- Enables regional and artist-based analysis

#### ⏰ time
Breaks timestamps into analytical units:
- hour, day, week, month, year, weekday
- Enables time-based trend analysis (peak listening hours, daily patterns)

---

#### 🚀 ETL Pipeline Design

The ETL pipeline follows a **two-stage process optimized for Redshift performance**:


#### 1️⃣ Stage 1: Load from S3 → Staging Tables

Raw JSON data is first loaded into staging tables:

- `staging_events`
- `staging_songs`

This step uses the Redshift `COPY` command to:

- Efficiently ingest large-scale data from S3
- Leverage parallel loading for performance
- Preserve raw data before transformation

#### 2️⃣ Stage 2: Transform → Analytics Tables

Data is transformed from staging tables into the star schema:

- Filtering only valid song play events (`page = 'NextSong'`)
- Joining event data with song metadata
- Extracting time attributes from timestamps
- Populating fact and dimension tables


---

### Question
**3. Provide example queries and results for song play analysis.**

#### Answer

Below are example analytical queries run on the Sparkify database, along with their results.


### 🎵 1. What is the most played song?

```sql
SELECT
    songs.title,
    COUNT(*) AS play_count
FROM songplays
JOIN songs ON songplays.song_id = songs.song_id
GROUP BY songs.title
ORDER BY play_count DESC
LIMIT 1;
```

```markdown id="r2"
Result:

You're The One with 37 songs played
```


### 📊 2. When is the highest usage time of day by hour for songs?

```sql
SELECT
    extract(hour FROM start_time) AS hour,
    count(songplay_id) AS total_plays
FROM
    songplays
GROUP BY hour
ORDER BY total_plays DESC;
```

```
Result:

Peak Hour: 16:00 with 542 plays

```


### 🌍 3. How does listening behavior vary by region?

```sql
SELECT
    location,
    COUNT(DISTINCT user_id) AS active_users,
    COUNT(*) AS total_plays,
    COUNT(*) * 1.0 / COUNT(DISTINCT user_id) AS avg_plays_per_user
FROM songplays
GROUP BY location
ORDER BY total_plays DESC
LIMIT 5;
```

```
Result:

| Region                                   | Active Users | Total Plays | Avg. Plays per User |
|------------------------------------------|-------------:|------------:|--------------------:|
| San Francisco-Oakland-Hayward, CA        | 2            | 691         | 345.50              |
| Portland-South Portland, ME              | 1            | 665         | 665.00              |
| Lansing-East Lansing, MI                 | 1            | 557         | 557.00              |
| Chicago-Naperville-Elgin, IL-IN-WI       | 3            | 475         | 158.33              |
| Atlanta-Sandy Springs-Roswell, GA        | 3            | 456         | 152.00              |
```

### 🔥 4. Do paid users have longer/more active sessions?

```sql
SELECT
    level,
    COUNT(*) * 1.0 / COUNT(DISTINCT session_id) AS avg_plays_per_session
FROM songplays
GROUP BY level;
```

```
Result:

free  | 2.0937 avg plays per session  
paid  | 28.3807 avg plays per session
```

### ⏱️ 5.How long do users wait before coming back to listen again?

```sql
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
```

```
Result:
Average return gap: 2.46 days
```
