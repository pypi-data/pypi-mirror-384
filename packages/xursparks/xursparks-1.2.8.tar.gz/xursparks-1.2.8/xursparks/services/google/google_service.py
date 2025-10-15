from .main import XGoogleDriveReader as gdr
from ...tools.logger import Logger as logger
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType

class XGoogleService:
    def __init__(self, dataStorage: dict = None, readOptions: dict = None, schema: StructType = None,
                 sparkSession: SparkSession = None):
        self.dataStorage = dataStorage
        self.readOptions = readOptions
        self.schema = schema
        # Initialize Spark session
        self.spark = sparkSession

    def processRequest(self):
        """
        Process the request to get data from Google Sheets.
        
        Returns:
            pyspark.sql.DataFrame: Spark DataFrame if available, otherwise None.
        """
        dataStorage = self.dataStorage
        readOptions = self.readOptions
        file_path = dataStorage.get("file_path")
        sheet_name = dataStorage.get("sheet_name", None)
        range_name = dataStorage.get("range_name", None)
        auth_file_path = dataStorage.get("auth_file_path", None)

        # Initialize Google Drive Reader
        if auth_file_path:
            reader = gdr(auth_file_path)
        else:
            reader = gdr()  # Use default auth file path

        # Authenticate
        if reader.authenticate():
            if dataStorage.get("format").upper().endswith("SHEETS"):
                print(f'GoogleService[processRequest]: Google Sheets executing sheet reading.')
                pandas_df = reader.read_sheet(
                    file_path=file_path,
                    sheet_name=sheet_name,
                    range_name=range_name
                )
                if pandas_df is not None:
                    # Convert pandas DataFrame to Spark DataFrame
                    try:
                        spark_df = self.spark.createDataFrame(
                            pandas_df,
                            schema=self.schema
                        )
                        logger().log(f'GoogleService[processRequest]: Spark DataFrame created with schema: {spark_df.schema}', level='debug')
                        return spark_df
                    except Exception as e:
                        logger().log(f'GoogleService[processRequest]: Failed to convert to Spark DataFrame: {str(e)}', level='error')
                        return None
                else:
                    logger().log('GoogleService[processRequest]: No data found in the specified sheet.', level='warning')
                    return None
            elif dataStorage.get("format").upper().endswith("FILE"):
                # Implement Google Drive File Download format handling if needed
                print(f'GoogleService[processRequest]: Google Drive File Download executing download.')
                print(f'GoogleService[processRequest]: file_path={file_path}')
                print(f'GoogleService[processRequest]: local_path={readOptions.get("local_path", "downloaded_file")}')
                reader.download_file(
                    file_path=file_path,
                    local_path=readOptions.get("local_path", "downloaded_file"),
                    mime_type=readOptions.get("mime_type", None)
                )
            else:
                logger().log('GoogleService[processRequest]: Unsupported format specified.', level='error')
                return None
        else:
            logger().log('GoogleService[processRequest]: Authentication failed.', level='error')
            return None
