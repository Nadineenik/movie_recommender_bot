from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)        # Название книги
    author = Column(String)                        # Автор
    description = Column(String)                   # Описание (для TF-IDF)
    genres = Column(String)                        # Жанры через запятую, например: "фантастика,драма"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)     # Уникальный ID из Telegram

class UserBook(Base):
    __tablename__ = 'user_books'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    book_id = Column(Integer, ForeignKey('books.id'))

    # Связь, чтобы при получении UserBook обращаться к actual Book
    book = relationship("Book")
