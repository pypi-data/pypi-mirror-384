from sqlalchemy                 import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from datetime                   import datetime

Base = declarative_base()

class Chapter(Base):
    __tablename__ = 'chapters'
    
    id = Column(Integer, primary_key=True)
    volume = Column(Integer)
    chapter = Column(Integer)
    title = Column(String)
    url = Column(Text)
    mirror_url = Column(Text)  # Alternative URL if telegra.ph is not accessible
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    def __repr__(self):
        return f"<Chapter(volume={self.volume}, chapter={self.chapter}, title={self.title})>"
    
class TocURL(Base):
    __tablename__ = 'ToC_url'

    id = Column(Integer, primary_key=True)
    manga_name = Column(String)
    url = Column(Text)
    mirror_url = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    def __repr__(self):
        return (
            f"<ToC_url(url={self.url}, "
            f"mirror_url={self.mirror_url}, "
            f"manga_name={self.manga_name})>"
        )