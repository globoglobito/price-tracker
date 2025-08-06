"""
FastAPI application for Price Tracker Search API
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from api.database.connection import get_db
from api.models.search import Search
from api.schemas.search import SearchCreate, SearchResponse, SearchUpdate, SearchListResponse
from api.crud import search as search_crud

# Create FastAPI app
app = FastAPI(
    title="Price Tracker Search API",
    description="API for managing search terms for price tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "message": "Price Tracker Search API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "price-tracker-search-api",
        "version": "1.0.0"
    }

@app.get("/searches", response_model=SearchListResponse, tags=["Searches"])
async def list_searches(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all search terms with optional filtering
    """
    searches = search_crud.get_searches(db, skip=skip, limit=limit, active_only=active_only)
    total = search_crud.get_searches_count(db, active_only=active_only)
    active_count = search_crud.get_searches_count(db, active_only=True)
    
    return SearchListResponse(
        searches=searches,
        total=total,
        active_count=active_count
    )

@app.post("/searches", response_model=SearchResponse, status_code=status.HTTP_201_CREATED, tags=["Searches"])
async def create_search(
    search: SearchCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new search term
    """
    # Check if search term already exists for this website
    existing_search = search_crud.get_search_by_term_and_website(
        db, search.search_term, search.website
    )
    if existing_search:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Search term '{search.search_term}' already exists for website '{search.website}'"
        )
    
    return search_crud.create_search(db=db, search=search)

@app.get("/searches/{search_id}", response_model=SearchResponse, tags=["Searches"])
async def get_search(search_id: int, db: Session = Depends(get_db)):
    """
    Get a specific search term by ID
    """
    search = search_crud.get_search(db, search_id=search_id)
    if search is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search with ID {search_id} not found"
        )
    return search

@app.put("/searches/{search_id}", response_model=SearchResponse, tags=["Searches"])
async def update_search(
    search_id: int,
    search_update: SearchUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a search term
    """
    search = search_crud.update_search(db=db, search_id=search_id, search_update=search_update)
    if search is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search with ID {search_id} not found"
        )
    return search

@app.delete("/searches/{search_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Searches"])
async def delete_search(search_id: int, db: Session = Depends(get_db)):
    """
    Delete a search term
    """
    success = search_crud.delete_search(db=db, search_id=search_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search with ID {search_id} not found"
        )

@app.patch("/searches/{search_id}/toggle", response_model=SearchResponse, tags=["Searches"])
async def toggle_search_status(search_id: int, db: Session = Depends(get_db)):
    """
    Toggle the active status of a search term
    """
    search = search_crud.toggle_search_status(db=db, search_id=search_id)
    if search is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search with ID {search_id} not found"
        )
    return search

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 