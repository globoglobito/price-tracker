"""
SQLAlchemy model for searches table
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from api.database.connection import Base

class Search(Base):
    """
    Search model representing the searches table
    """
    __tablename__ = "searches"
    __table_args__ = {"schema": "price_tracker"}

    id = Column(Integer, primary_key=True, index=True)
    search_term = Column(String(200), nullable=False, index=True)
    website = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Unique constraint on search_term and website combination
    __table_args__ = (
        UniqueConstraint('search_term', 'website', name='searches_search_term_website_key'),
        {"schema": "price_tracker"}
    )

    def __repr__(self):
        return f"<Search(id={self.id}, search_term='{self.search_term}', website='{self.website}', is_active={self.is_active})>" 