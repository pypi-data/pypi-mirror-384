# This module previously contained custom exception handling classes.
# All custom exception handling has been removed in favor of FastAPI's built-in exception handling.
#
# Services should now use FastAPI's HTTPException directly:
#
# from fastapi import HTTPException
#
# # Example usage:
# raise HTTPException(status_code=404, detail="Resource not found")
# raise HTTPException(status_code=400, detail="Invalid input data")
# raise HTTPException(status_code=403, detail="Access forbidden")
# raise HTTPException(status_code=409, detail="Resource already exists")
# raise HTTPException(status_code=422, detail="Validation error")
# raise HTTPException(status_code=500, detail="Internal server error")
#
# FastAPI will automatically handle these exceptions and return appropriate JSON responses.
