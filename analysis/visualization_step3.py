import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
import os

DB_PARAMS = {
    'dbname': 'movies_db',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

def fetch_data(query):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            data = cur.fetchall()
            
            column_names = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(data, columns=column_names)

def create_visualizations():
    try:
        os.makedirs('analysis/plots', exist_ok=True)
        
        plt.style.use('default')
        sns.set_theme()
        
        time_analysis()
        
        genre_analysis()
        
        avg_rating_analysis()
        
        personnel_analysis()
        
        misc_analysis()
        
        print('Все визуализации успешно созданы')
        
    except Exception as e:
        print('error: ', str(e))
        raise

def time_analysis():
    try:
        query = """
        select 
                extract(year from creation_date) as year,
                count(*) as film_count,
                avg(rating) as avg_rating
        from analytics.film_aggregated
        where creation_date is not null
        group by year
        order by year;
        """
        
        df = fetch_data(query)
        
        if df.empty:
            print("Нет данных, т/к строки по колонке creation_date NULL")
            return
            
        print(df.head())
        
        plt.figure(figsize=(12, 6))
        plt.bar(df['year'], df['film_count'])
        plt.title('Количество фильмов по годам')
        plt.xlabel('Год')
        plt.ylabel('Количество фильмов')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('analysis/plots/films_by_year.png')
        plt.close()
        
        plt.figure(figsize=(12, 6))
        plt.plot(df['year'], df['avg_rating'], marker='o')
        plt.title('Динамика средней оценки фильмов по годам')
        plt.xlabel('Год')
        plt.ylabel('Средняя оценка')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('analysis/plots/ratings_by_year.png')
        plt.close()
        
    except Exception as e:
        print('error: ', str(e))
        raise

def genre_analysis():
    try:
        query = """
        select 
            unnest(genres) as genre,
            count(*) as film_count
        from analytics.film_aggregated
        group by genre
        order by film_count desc;
        """
        
        df = fetch_data(query)
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='genre', y='film_count')
        plt.title('Количество фильмов по жанрам')
        plt.xlabel('Жанр')
        plt.ylabel('Количество фильмов')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('analysis/plots/films_by_genre.png')
        plt.close()
        
        plt.figure(figsize=(12, 6))
        top_10 = df.head(10)
        sns.barplot(data=top_10, x='genre', y='film_count')
        plt.title('Топ-10 самых популярных жанров')
        plt.xlabel('Жанр')
        plt.ylabel('Количество фильмов')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('analysis/plots/top_10_genres.png')
        plt.close()
        
    except Exception as e:
        print('error: ', str(e))
        raise

def avg_rating_analysis():
    try:
        query = """
        select 
            unnest(genres) as genre,
            round(avg(rating)::numeric, 2) as avg_rating,
            count(*) as film_count
        from analytics.film_aggregated
        where rating is not null
        group by genre
        order by avg_rating desc;
        """
        
        df = fetch_data(query)
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='genre', y='avg_rating')
        plt.title('Средняя оценка по жанрам')
        plt.xlabel('Жанр')
        plt.ylabel('Средняя оценка')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('analysis/plots/genre_ratings.png')
        plt.close()
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='genre', y='avg_rating')
        plt.title('Средняя оценка по жанрам (с количеством фильмов)')
        plt.xlabel('Жанр')
        plt.ylabel('Средняя оценка')
        plt.xticks(rotation=45)
        
        for i, row in df.iterrows():
            plt.text(i, row['avg_rating'], f'n={row["film_count"]}', 
                    ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('analysis/plots/genre_ratings_with_count.png')
        plt.close()
        
    except Exception as e:
        print('error: ', str(e))
        raise

def personnel_analysis():
    try:
        query = """
        select 
            'actor' as role,
            count(*) as count
        from analytics.film_aggregated,
        unnest(actors) as actor
        group by role
        union all
        select 
            'director' as role,
            count(*) as count
        from analytics.film_aggregated,
        unnest(directors) as director
        group by role
        union all
        select 
            'writer' as role,
            count(*) as count
        from analytics.film_aggregated,
        unnest(writers) as writer
        group by role;
        """
        
        df_roles = fetch_data(query)
        
        plt.figure(figsize=(10, 6))
        plt.pie(df_roles['count'], labels=df_roles['role'], autopct='%1.1f%%')
        plt.title('Распределение ролей')
        plt.tight_layout()
        plt.savefig('analysis/plots/role_distribution.png')
        plt.close()
        
        query = """
        select 
            actor,
            count(*) as film_count
        from analytics.film_aggregated,
        unnest(actors) as actor
        group by actor
        order by film_count desc
        limit 10;
        """
        
        df_actors = fetch_data(query)
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df_actors, x='actor', y='film_count')
        plt.title('Топ-10 актёров по количеству фильмов')
        plt.xlabel('Актёр')
        plt.ylabel('Количество фильмов')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('analysis/plots/top_10_actors.png')
        plt.close()
        
    except Exception as e:
        print('error: ', str(e))
        raise

def misc_analysis():
    try:
        query = """
        select 
            rating,
            type
        from analytics.film_aggregated
        where rating is not null;
        """
        
        df = fetch_data(query)
        
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x='rating', bins=20)
        plt.title('Распределение оценок фильмов')
        plt.xlabel('Оценка')
        plt.ylabel('Количество фильмов')
        plt.tight_layout()
        plt.savefig('analysis/plots/rating_distribution.png')
        plt.close()
        
        type_counts = df['type'].value_counts()
        plt.figure(figsize=(10, 6))
        plt.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%')
        plt.title('Распределение фильмов по типу')
        plt.tight_layout()
        plt.savefig('analysis/plots/type_distribution.png')
        plt.close()
        
    except Exception as e:
        print('error: ', str(e))
        raise

if __name__ == "__main__":
    create_visualizations() 