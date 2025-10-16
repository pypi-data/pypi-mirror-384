"""Public API endpoints that don't require authentication."""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException

from ..services.filesystem_thoughts import get_filesystem_thoughts, get_filesystem_thought_by_id, update_filesystem_thought

router = APIRouter()


@router.get("/thoughts/local")
async def list_local_thoughts(
    search: Optional[str] = Query(None, description="Search in title and content"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    repository: Optional[str] = Query(None, description="Filter by repository"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of thoughts to return"),
):
    """List thoughts directly from local filesystem (no authentication required)."""
    
    thoughts = get_filesystem_thoughts(
        search=search,
        tags=tags,
        repository=repository,
        limit=limit
    )
    
    from pathlib import Path
    current_dir = Path.cwd()
    
    # Use the same path detection logic as get_filesystem_thoughts
    if current_dir.name == "backend":
        parent_dir = current_dir.parent
    elif current_dir.name == "src":  # Docker: running from /app/backend/src
        # In Docker, check if thoughts are mounted at /app/thoughts
        docker_thoughts = Path("/app/thoughts")
        if docker_thoughts.exists():
            parent_dir = Path("/app")
        else:
            # Fallback to going up two levels: /app/backend/src -> /app
            parent_dir = current_dir.parent.parent
    else:
        parent_dir = current_dir
    
    return {
        "thoughts": thoughts,
        "total": len(thoughts),
        "source": "local-filesystem",
        "repositories_found": list(set(t.get("repository", "unknown") for t in thoughts)),
        "debug_info": {
            "current_working_directory": str(current_dir),
            "search_directory": str(parent_dir),
            "thoughts_directory_exists": (parent_dir / "thoughts").exists(),
            "thoughts_directory_contents": list(str(p) for p in (parent_dir / "thoughts").iterdir()) if (parent_dir / "thoughts").exists() else [],
            "hot_reload_test": "working_after_restart"
        }
    }


@router.get("/thoughts/local/{thought_id}")
async def get_local_thought(thought_id: str):
    """Get a specific thought directly from local filesystem by its hash ID."""
    
    thought = get_filesystem_thought_by_id(thought_id)
    if not thought:
        raise HTTPException(status_code=404, detail=f"Thought with ID {thought_id} not found")
    
    return thought


@router.put("/thoughts/local/{thought_id}")
async def update_local_thought(thought_id: str, request: dict):
    """Update a specific thought on the local filesystem."""
    
    # Extract content from request
    content = request.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # Update the thought
    updated_thought = update_filesystem_thought(thought_id, content)
    if not updated_thought:
        raise HTTPException(status_code=404, detail=f"Thought with ID {thought_id} not found or could not be updated")
    
    return updated_thought