from typing import TypedDict, List, Optional

class ColumnInfo(TypedDict):
    Name: Optional[str]
    Type: dict  # Add detailed types for nested fields if needed, e.g., for ScalarType or TimeSeriesType

class Datum(TypedDict):
    ScalarValue: Optional[str]
    TimeSeriesValue: Optional[List[dict]]  # Add detailed types if needed
    ArrayValue: Optional[List[dict]]  # Add detailed types if needed
    RowValue: Optional[dict]  # Add detailed types for nested row structure

class Row(TypedDict):
    Data: List[Datum]

class QueryResponse(TypedDict):
    QueryId: str
    NextToken: Optional[str]
    ColumnInfo: List[ColumnInfo]
    Rows: List[Row]
    QueryStatus: dict  # Add detailed types if needed, e.g., for ProgressPercentage, CumulativeBytesScanned
