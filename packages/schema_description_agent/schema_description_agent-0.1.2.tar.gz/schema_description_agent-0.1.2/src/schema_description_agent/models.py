
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ColumnDescription(BaseModel):
    name: str
    description: str

class TableDescription(BaseModel):
    table_name: str
    description: str
    columns: List[ColumnDescription]

class SchemaDescription(BaseModel):
    tables: List[TableDescription]
