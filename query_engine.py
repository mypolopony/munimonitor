import boto3
import pandas as pd
from typing import Dict, Any
from botocore.config import Config

class QueryEngine():
    def __init__(self, database_name: str, table_name: str):
        self.database = database_name
        self.table = table_name
        self.client = boto3.client("timestream-query", region_name="us-west-2")
    
    def _response_to_pandas(self, response: Dict[str, Any]) -> pd.DataFrame:
        """
        Processes the raw Timestream response rows and maps column names to values.

        Parameters
        ----------
        response : Dict[str, Any]
            The raw Timestream query response
        
        Returns
        -------
        pd.DataFrame
            The processed response as a Pandas DataFrame
        """
        column_names = [column["Name"] for column in response["ColumnInfo"]]
        rows = response["Rows"]

        processed_rows = []
        for row in rows:
            data = row["Data"]
            processed_row = {
                column_names[i]: (
                    data[i].get("ScalarValue", None)
                )
                for i in range(len(column_names))
            }
            processed_rows.append(processed_row)
        
        return pd.DataFrame(processed_rows)
    
    def get_full_query_results(self, query_string: str) -> Dict[str, Any]:
        """
        Fetches the full results of a Timestream query by handling pagination and completion.

        Parameters
        ----------
        query_string : str
            The query string to execute
        
        Returns
        -------
        Dict[str, Any]
            The full query response
        """
        print(f"Executing Query...\n\t{query_string}")

        query_results = []
        next_token = None

        while True:
            # Perform the query or fetch the next set of results
            if next_token:
                response = self.client.query(QueryString=query_string, NextToken=next_token)
            else:
                response = self.client.query(QueryString=query_string)

            # Append rows to the results
            query_results.extend(response.get("Rows", []))

            # Check for NextToken to continue fetching more results
            next_token = response.get("NextToken")
            if not next_token:
                break  # No more pages, query is complete

            # Display query progress
            progress = response.get("QueryStatus", {}).get("ProgressPercentage", 0)
            print(f"Query progress: {progress}%")

        return query_results


class VehiclePositions(QueryEngine):
    def __init__(self):
        super().__init__("gtfs_data", "vehicle_positions")
        self.valid_columns = ["time", "route_id", "vehicle_id", "latitude", "longitude", "speed"]

    def query(self, columns_to_return: list[str], where_clause: str="") -> pd.DataFrame:
        """
        Gather vehicle position data from the Timestream table.

        Parameters
        ----------
        columns_to_return : List[str]
            The columns to return in the query
        
        Returns
        -------
        pd.DataFrame
            The query results as a Pandas DataFrame
        """
        # Validate the columns to return
        if not set(columns_to_return).issubset(self.valid_columns):
            raise ValueError("Invalid columns specified. Valid columns are: ", self.valid_columns)

        # Add the WHERE clause if provided
        if where_clause:
            where_clause = f"WHERE {where_clause}"
    
        # Construct the query
        query = f"""
        SELECT DISTINCT {", ".join(columns_to_return)}
        FROM "{self.database}"."{self.table}"
        {where_clause}
        """

        # Execute the query and return the results as a Pandas DataFrame
        response = self.get_full_query_results(query)
        self.dataframe = self._response_to_pandas(response)

        return self.dataframe
    
    def create_geofence(self):
        pass