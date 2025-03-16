from typing import Any, Dict, List, Union
import datetime
from pydantic import BaseModel

def to_serializable_dict(obj: Any) -> Any:
    """
    Recursively convert an object into a JSON serializable dictionary.
    
    Args:
        obj: Any Python object to be converted
        
    Returns:
        A JSON serializable representation of the object
    """
    # Handle None
    if obj is None:
        return None
        
    # Handle basic types that are already JSON serializable
    if isinstance(obj, (str, int, float, bool)):
        return obj
        
    # Handle datetime objects
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
        
    # Handle Pydantic models
    if isinstance(obj, BaseModel):
        return to_serializable_dict(obj.model_dump())
        
    # Handle dictionaries
    if isinstance(obj, dict):
        return {k: to_serializable_dict(v) for k, v in obj.items()}
        
    # Handle lists, tuples and sets
    if isinstance(obj, (list, tuple, set)):
        return [to_serializable_dict(item) for item in obj]
    
    # Handle objects with to_dict() method
    if hasattr(obj, 'to_dict'):
        return to_serializable_dict(obj.to_dict())
        
    # Handle objects with __dict__ attribute (most custom classes)
    if hasattr(obj, '__dict__'):
        return to_serializable_dict(vars(obj))
            
    # Try to convert to string as a last resort
    try:
        return str(obj)
    except Exception:
        return f'<Object of type {type(obj).__name__} could not be serialized>'
