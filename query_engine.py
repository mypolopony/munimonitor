import boto3
import pandas as pd
from typing import Dict, List, Any
from botocore.config import Config

class TSQueryEngine():
    def __init__(self, database_name: str, table_name: str):
        self.database = database_name
        self.table = table_name
        self.client = boto3.client("timestream-query", region_name="us-west-2")

    def _force_pandas_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Change the Pandas DataFrame column types to match the expected types.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to update
        
        Returns
        -------
        pd.DataFrame
            The updated DataFrame
        """
        # Convert the time column to a datetime
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"])
        
        # Convert other columns to float
        for column in ["latitude", "longitude", "speed"]:
            if column in df.columns:
                df[column] = df[column].astype(float)
        
        return df
    
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
        rows = response["Rows"]
        columns = [col["Name"] for col in response["ColumnInfo"]]

        processed_rows = []
        for row in rows:
            data = row["Data"]
            processed_row = {
                columns[i]: (
                    data[i].get("ScalarValue", None)
                )
                for i in range(len(columns))
            }
            processed_rows.append(processed_row)
        
        return self._force_pandas_types(pd.DataFrame(processed_rows, columns=columns))
    
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

        # Try fetching the first set of results
        response = self.client.query(QueryString=query_string)
        next_token = response.get("NextToken", "")

        # Continue fetching results until the query is complete
        if next_token:
            while True:
                # If we have a NextToken, use it to fetch the next set of results
                response = self.client.query(QueryString=query_string, NextToken=response.get("NextToken", ""))
                
                # We're complete
                if response["QueryStatus"]["ProgressPercentage"] == 100:
                    break

            # Display query progress
            progress = response.get("QueryStatus", {}).get("ProgressPercentage", 0)
            print(f"Query progress: {progress:.2f}%")

        return response


class VehiclePositions(TSQueryEngine):
    def __init__(self):
        super().__init__("gtfs_data", "vehicle_positions")
        self.valid_columns = ["time", "trip_id", "route_id", "vehicle_id", "latitude", "longitude", "speed"]

    def query(self, columns_to_return: List[str], where_clause: str="") -> pd.DataFrame:
        """
        Gather vehicle position data from the Timestream table.

        Parameters
        ----------
        columns_to_return : List[str]
            The columns to return in the query
        where_clause : str
            The WHERE clause to filter the query
        
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