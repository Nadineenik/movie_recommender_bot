from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
from joblib import dump, load
from database.db import SessionLocal, Book  # или через session

# Если у тебя есть список русских стоп-слов – прокинь его сюда. 
russian_stop_words = [...]  # можно взять из nltk или собрать вручную.

class RecommenderSystem:
    def __init__(self, model_filename='tfidf_model.joblib'):
        self.tfidf = TfidfVectorizer(stop_words=russian_stop_words)
        self.model_filename = model_filename
        self.update_model()

    def update_model(self, force_update: bool = False):
        """
        Если есть сохранённый файл с моделью (tfidf_matrix,tfidf,df) – загружаем его.
        Иначе:
          - Берём все книги из базы (id, description, genres).
          - Строим колонку content = description + ' ' + genres
          - Фитим TF-IDF на этой колонке и сохраняем (joblib.dump).
        """
        if not force_update:
            try:
                self.tfidf_matrix, self.tfidf, self.df = load(self.model_filename)
                return
            except FileNotFoundError:
                pass

        # Если модели нет – создаём заново:
        with SessionLocal() as session:
            books = session.query(Book.id, Book.description, Book.genres).all()
        df = pd.DataFrame(
            [(b.id, b.description or '', b.genres or '') for b in books],
            columns=['id', 'description', 'genres']
        )
        # Собираем контент: описание + жанры (жанры через пробел)
        df['content'] = df['description'] + ' ' + df['genres'].replace(',', ' ')
        self.tfidf_matrix = self.tfidf.fit_transform(df['content'])
        self.df = df
        dump((self.tfidf_matrix, self.tfidf, self.df), self.model_filename)

    def get_recommendations(self, read_book_ids: list[int], top_n: int = 5) -> list[int]:
        """
        Принимаем список ID уже прочитанных книг (read_book_ids).
        Строим «профиль пользователя» как среднее TF-IDF-векторов прочитанных книг.
        Считаем косинусное сходство между профилем и всеми векторами книг.
        Возвращаем top_n ID книг, исключая уже прочитанные.
        """
        idxs = self.df[self.df['id'].isin(read_book_ids)].index
        if len(idxs) == 0:
            # Если юзер ещё ничего не читал, можно возвращать топ популярных
            # (тут можно потом докинуть сортировку по количеству отметок read)
            return []

        user_profile = np.asarray(self.tfidf_matrix[idxs].mean(axis=0))[0]
        sims = cosine_similarity([user_profile], self.tfidf_matrix)[0]
        candidates = np.argsort(-sims)
        rec_idxs = [i for i in candidates if i not in idxs][:top_n]
        return self.df['id'].iloc[rec_idxs].tolist()
