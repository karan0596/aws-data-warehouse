import configparser
import psycopg2
from sql_queries import copy_table_queries, insert_table_queries
from sql_queries import (
    most_played_song_query,
    peak_hour_query,
    regional_behavior_query,
    user_level_session_query,
    return_time_query
)


def load_staging_tables(cur, conn):
    """ Load data into the staging tables. 
    
    Args: 
        cur: Database cursor for executing SQL queries. 
        conn: Database connection for committing changes.
    
    """
    for query in copy_table_queries:
        cur.execute(query)
        conn.commit()


def insert_tables(cur, conn):
    """ Insert data from the staging tables into the analytics tables. 
    
    Args: 
        cur: Database cursor for executing SQL queries. 
        conn: Database connection for committing changes. 
    """
    
    for query in insert_table_queries:
        cur.execute(query)
        conn.commit()
        

        
def run_analytics(cur, conn):
    """
    Run predefined analytics queries and print a report.

    Args:
        cur: Database cursor for executing SQL queries.
        conn: Database connection for committing changes.
    """
    
    print("\n================ ANALYTICS REPORT ================\n")

    # 1. Most played song
    cur.execute(most_played_song_query)
    song_id, title, count = cur.fetchone()
    print(f"\n1. Most played song: {title} ({song_id}) with {count} plays")

    # 2. Peak hour
    cur.execute(peak_hour_query)
    hour, total_plays = cur.fetchone()
    print(f"\n2. Peak hour: {int(hour):02d}:00 with {total_plays} plays")

    # 3. Regional behavior
    cur.execute(regional_behavior_query)
    results = cur.fetchall()
    print("\n3. Listening Behavior by Region:")
    for location, users, total_plays, avg_per_user in results:
        print(f"Region: {location}")
        print(f"  Active Users: {users}")
        print(f"  Total Plays: {total_plays}")
        print(f"  Avg Plays per User: {avg_per_user:.2f}")
        print("-" * 50)

    # 4. Paid vs free users
    cur.execute(user_level_session_query)
    results = cur.fetchall()
    print("\n4. Paid vs Free Users (avg plays per session):")
    for level, value in results:
        print(f"{level}\t{float(value):.2f}")

    # 5. Return time
    cur.execute(return_time_query)
    result = cur.fetchone()[0]
    print("\n5. Across all users, the average time between one session ending and the next session is:")
    print(f"{result} days")

    print("\n==================================================\n")
    
    

def main():
    """ 
    Load data, populate the analytics tables, and run analytics queries. 
    
    """
    
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()
    
    load_staging_tables(cur, conn)
    insert_tables(cur, conn)
    
    run_analytics(cur, conn)

    conn.close()


if __name__ == "__main__":
    main()