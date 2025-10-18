from typing import Union
from pydantic import BaseModel

class TableQuery(BaseModel):
    name: str
    column_name: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_pass: str

