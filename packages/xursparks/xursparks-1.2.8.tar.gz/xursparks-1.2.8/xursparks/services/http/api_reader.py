from xursparks.services.http.api_service import APIService
import pandas as pd
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, BooleanType

class APIReader:
    """
    A class to read and process API data.
    """

    def __init__(self, api_url: str = None,
                 args: dict = None,
                 spark_session: object = None,
                 data: object = None):
        self.api_url = api_url
        self.args = args
        self.spark_session = spark_session
        self.data = data

    def fetch_data(self):
        headers = self.args.get("headers")
        if headers and "Authorization" in headers:
            # Remove old Authorization if exists
            headers.pop("Authorization")
            
            # Get new Authorization value
            auth_value = self.args.get("key")
            if auth_value:
                # Add new Authorization with updated value
                headers["Authorization"] = f"{auth_value}"
                print(f"Updated Authorization header with new token")
        
        print(f"[xurspasrks.http.api_reader][fetch_data] Headers: {headers}")

        api_service = APIService(base_url=self.args.get("base_url"), args={
            "auth": self.args.get("auth"),
            "headers": headers,
            "method": self.args.get("method", "GET"),
            "verify_ssl": self.args.get("verify_ssl", False),
        })

        return api_service.processRequest()

    def process_data(self, df:object = None):
        """
        Process the fetched data and convert to Spark DataFrame.
        
        Args:
            df: Optional DataFrame to process
            
        Returns:
            pyspark.sql.DataFrame: Processed Spark DataFrame
        """
        if self.data:
            # Create Pandas DataFrame
            panda_frame = pd.DataFrame(self.data)
            
            # Create StructType schema
            schema_fields = []
            for column, dtype in panda_frame.dtypes.items():
                if dtype == 'object':
                    field_type = StringType()
                elif dtype == 'float64':
                    field_type = DoubleType()
                elif dtype == 'int64':
                    field_type = IntegerType()
                elif dtype == 'bool':
                    field_type = BooleanType()
                else:
                    field_type = StringType()  # Default to string
                    
                schema_fields.append(StructField(column, field_type, True))
            
            schema = StructType(schema_fields)
            
            # Create Spark DataFrame with schema
            try:
                spark_df = self.spark_session.createDataFrame(
                    panda_frame,
                    schema=schema
                )
                #print("\nSpark DataFrame Schema:")
                #spark_df.printSchema()
                return spark_df
                
            except Exception as e:
                print(f"Error converting to Spark DataFrame: {str(e)}")
                return None
        
        return df
