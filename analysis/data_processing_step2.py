import pandas as pd
import psycopg2
from datetime import datetime
import io


DB_PARAMS = {
    'dbname': 'movies_db',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

def create_aggregated_table():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""create schema if not exists analytics;""")
            
            cur.execute("""
                create table if not exists analytics.film_aggregated (
                    id uuid primary key,
                    title text,
                    description text,
                    creation_date date,
                    rating float,
                    type text,
                    genres text[],
                    actors text[],
                    directors text[],
                    writers text[]
                );
            """)
            
            cur.execute("""truncate table analytics.film_aggregated;""")
            
            cur.execute("""
                insert into analytics.film_aggregated
                select 
                    fw.id,
                    fw.title,
                    fw.description,
                    fw.creation_date,
                    fw.rating,
                    fw.type,
                    array_agg(distinct g.name) as genres,
                    array_agg(distinct case when pfw.role = 'actor' then p.full_name end) filter (where pfw.role = 'actor') as actors,
                    array_agg(distinct case when pfw.role = 'director' then p.full_name end) filter (where pfw.role = 'director') as directors,
                    array_agg(distinct case when pfw.role = 'writer' then p.full_name end) filter (where pfw.role = 'writer') as writers
                from content.film_work fw
                left join content.genre_film_work gfw on fw.id = gfw.film_work_id
                left join content.genre g on gfw.genre_id = g.id
                left join content.person_film_work pfw on fw.id = pfw.film_work_id
                left join content.person p on pfw.person_id = p.id
                group by fw.id, fw.title, fw.description, fw.creation_date, fw.rating, fw.type;
            """)
    
            conn.commit()
            print('Агрегированная таблица создана')

def fetch_film_data():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                select 
                    id,
                    title,
                    description,
                    creation_date,
                    rating,
                    type,
                    genres,
                    actors,
                    directors,
                    writers
                from analytics.film_aggregated;
            """)
            return cur.fetchall()

def process_film_data(data):
    df = pd.DataFrame(data, columns=[
        'id', 'title', 'description', 'creation_date', 
        'rating', 'type', 'genres', 'actors', 'directors', 'writers'
    ])

    array_columns = ['genres', 'actors', 'directors', 'writers']
    for col in array_columns:
        df[col] = df[col].apply(lambda x: x if x is not None else [])

    df['creation_date'] = pd.to_datetime(df['creation_date'])
    df['creation_date'] = df['creation_date'].where(pd.notnull(df['creation_date']), None)
    
    df['rating'] = pd.to_numeric(df['rating'])
    df['rating'] = df['rating'].where(pd.notnull(df['rating']), None)
    
    print('Базовая очистка и агрегация выполнены')
    
    return df

def save_to_database(df):
    for col in ['genres', 'actors', 'directors', 'writers']:
        df[col] = df[col].apply(lambda x: '{' + ','.join([f'"{item}"' for item in x]) + '}' if x else '{}')
    
    csv_buffer = io.StringIO()
    
    df.to_csv(csv_buffer, index=False, header=False, sep=',')
    
    csv_buffer.seek(0)
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""truncate table analytics.film_aggregated;""")
            
            cur.copy_expert(f"COPY analytics.film_aggregated FROM STDIN WITH CSV", csv_buffer)
            
            conn.commit()
            print(f'Загружено {len(df)} строк в таблицу')

def main():
    try:
        create_aggregated_table()
        
        data = fetch_film_data()
        
        df = process_film_data(data)
        
        save_to_database(df)
        
    except Exception as e:
        print('error: ', str(e))
        raise

if __name__ == "__main__":
    main() 