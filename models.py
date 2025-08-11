from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, JSON, Text as sqltext

class Base(DeclarativeBase):
    pass



class Source(Base):
    __tablename__ = 'source'
    source_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    type: Mapped[str] = mapped_column()
    page_count: Mapped[Optional[str]] = mapped_column(nullable=True)
    internal_links: Mapped[str] = mapped_column()
    base_url: Mapped[str] = mapped_column()
    page_content: Mapped[str] = mapped_column()


    texts = relationship("Text", back_populates="source", cascade="all, delete")
    media = relationship("Media", back_populates="source", cascade="all, delete")




class Text(Base):
    __tablename__ = 'text'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.source_id"), index=True)
    internal_link_url: Mapped[str] = mapped_column()
    text_content: Mapped[str] = mapped_column()
    source = relationship("Source", back_populates="texts")




class Media(Base):
    __tablename__ = 'media'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.source_id"), index=True)
    internal_link: Mapped[str] = mapped_column()
    media_url: Mapped[str] = mapped_column()
    meta_info: Mapped[Optional[str]] = mapped_column(nullable=True)
    type: Mapped[str] = mapped_column()
    source = relationship("Source", back_populates="media")




class Recursive_Text(Base):
    __tablename__ = 'recursive'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.source_id"), index=True)
    content: Mapped[str] = mapped_column(sqltext)
    embedding: Mapped[list[float]] = mapped_column(JSON)