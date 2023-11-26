from pydantic import BaseModel

class InputQuery(BaseModel):
    query: str
    session_id: str