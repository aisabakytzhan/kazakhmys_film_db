-- Убедиться в наличии связей "многие ко многим" между фильмами и жанрами
SELECT f.title, array_agg(g.name) as genres 
FROM content.film_work f 
JOIN content.genre_film_work gf ON f.id = gf.film_work_id 
JOIN content.genre g ON gf.genre_id = g.id 
GROUP BY f.title;

-- Убедиться в наличии связей "многие ко многим" между фильмами и участниками с ролями
SELECT f.title, p.full_name, pf.role 
FROM content.film_work f 
JOIN content.person_film_work pf ON f.id = pf.film_work_id 
JOIN content.person p ON pf.person_id = p.id;