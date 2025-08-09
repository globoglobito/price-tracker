"""
CRUD operations for searches table
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from api.models.search import Search
from api.schemas.search import SearchCreate, SearchUpdate

def get_search(db: Session, search_id: int) -> Optional[Search]:
    """Get a search by ID"""
    return db.query(Search).filter(Search.id == search_id).first()

def get_search_by_term_and_website(db: Session, search_term: str, website: str) -> Optional[Search]:
    """Get a search by search term and website combination"""
    return db.query(Search).filter(
        and_(Search.search_term == search_term, Search.website == website)
    ).first()

def get_searches(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = False
) -> List[Search]:
    """Get list of searches with optional filtering"""
    query = db.query(Search)
    
    if active_only:
        query = query.filter(Search.is_active == True)
    
    return query.offset(skip).limit(limit).all()

def get_searches_count(db: Session, active_only: bool = False) -> int:
    """Get total count of searches"""
    query = db.query(Search)
    
    if active_only:
        query = query.filter(Search.is_active == True)
    
    return query.count()

def create_search(db: Session, search: SearchCreate) -> Search:
    """Create a new search"""
    db_search = Search(
        search_term=search.search_term,
        website=search.website,
        is_active=search.is_active
    )
    db.add(db_search)
    db.commit()
    db.refresh(db_search)
    return db_search

def update_search(db: Session, search_id: int, search_update: SearchUpdate) -> Optional[Search]:
    """Update a search"""
    db_search = get_search(db, search_id)
    if not db_search:
        return None
    
    update_data = search_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_search, field, value)
    
    db.commit()
    db.refresh(db_search)
    return db_search

def delete_search(db: Session, search_id: int) -> bool:
    """Delete a search"""
    db_search = get_search(db, search_id)
    if not db_search:
        return False
    
    db.delete(db_search)
    db.commit()
    return True

def toggle_search_status(db: Session, search_id: int) -> Optional[Search]:
    """Toggle the active status of a search"""
    db_search = get_search(db, search_id)
    if not db_search:
        return None
    
    db_search.is_active = not db_search.is_active
    db.commit()
    db.refresh(db_search)
    return db_search 