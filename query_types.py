from typing import TypedDict, List, Optional

class ColumnInfo(TypedDict):
    Name: Optional[str]
    Type: dict 

class Datum(TypedDict):
    ScalarValue: Optional[str]
    TimeSeriesValue: Optional[List[dict]]
    ArrayValue: Optional[List[dict]]
    RowValue: Optional[dict]

class Row(TypedDict):
    Data: List[Datum]

class QueryResponse(TypedDict):
    QueryId: str
    NextToken: Optional[str]
    ColumnInfo: List[ColumnInfo]
    Rows: List[Row]
    QueryStatus: dict 
