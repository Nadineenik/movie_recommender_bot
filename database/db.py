from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker, joinedload
import config
from .models import Base, Book, User, UserBook

# Инициализируем движок (на основе config.DB_URL)
engine = create_engine(config.DB_URL, echo=False)  
SessionLocal = sessionmaker(bind=engine)

# Создаём таблицы, если они ещё не созданы:
Base.metadata.create_all(bind=engine)

class DB:
    def __init__(self):
        self.Session = SessionLocal

    def add_book(self, title: str, author: str, description: str, genres: str):
        """Добавление новой книги в таблицу books."""
        with self.Session() as session:
            book = Book(title=title, author=author, description=description, genres=genres)
            session.add(book)
            session.commit()

    def search_books(self, query: str) -> list[dict]:
        """
        Ищем книги, где в title или description встречается query.
        Возвращаем список словарей: {'id': ..., 'title': ..., 'author': ...}
        """
        with self.Session() as session:
            q = f"%{query}%"
            results = session.query(Book).filter(
                or_(Book.title.ilike(q), Book.description.ilike(q))
            ).all()
            return [
                {'id': b.id, 'title': b.title, 'author': b.author}
                for b in results
            ]

    def get_user_books(self, telegram_id: int) -> list[int]:
        """
        Получаем список ID книг, которые пользователь уже отметил как прочитанные.
        Если пользователь ещё не зарегистрирован в users, создаём его.
        """
        with self.Session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if not user:
                user = User(telegram_id=telegram_id)
                session.add(user)
                session.commit()
            rels = session.query(UserBook).options(joinedload(UserBook.book))\
                       .filter_by(user_id=user.id).all()
            return [rel.book.id for rel in rels]

    def add_user_book(self, telegram_id: int, book_id: int) -> bool:
        """
        Отмечаем книгу как прочитанную для данного пользователя.
        Возвращаем False, если такой UserBook уже существует (не дублируем).
        """
        with self.Session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if not user:
                user = User(telegram_id=telegram_id)
                session.add(user)
                session.commit()
            exists = session.query(UserBook).filter_by(
                user_id=user.id, book_id=book_id
            ).first()
            if exists:
                return False
            session.add(UserBook(user_id=user.id, book_id=book_id))
            session.commit()
            return True
