import os
import re
import pandas as pd
import xursparks

class ItemReader:

    def excel_file_reader(self, file_path: str):
        # Dictionary to store dataframes by sheet name
        tagged_dataframes = {}
        
        # Iterate through all files in the given directory
        for file in os.listdir(file_path):
            if file.endswith('.xlsx') or file.endswith('.xls'):
                # Extract the filename without the extension
                filename = os.path.splitext(file)[0]
                
                # Construct full file path
                full_file_path = os.path.join(file_path, file)
                
                # Read the Excel file
                excel_file = pd.ExcelFile(full_file_path)
                
                # Iterate over all sheet names in the Excel file
                for sheet_name in excel_file.sheet_names:
                    # Read each sheet into a dataframe
                    sheet_df = pd.read_excel(full_file_path, sheet_name=sheet_name)
                    sheet_df = sheet_df.astype(str)       

                    # Store the dataframe in the dictionary with the key as (filename, sheet_name)
                    tagged_dataframes[(filename, sheet_name)] = sheet_df
        
        return tagged_dataframes
    
    # create function for specific file

    # create function that gets data given keyword, then 2nd keyword, then no. columns

    def json_file_reader(self, file_path: str, file_name: str):
        # Compile the regex pattern for matching file names
        regex_pattern = re.compile(file_name)
        
        # Search for files in the directory that match the pattern and have .json extension
        matching_files = [f for f in os.listdir(file_path) if f.endswith('.json') and regex_pattern.search(f)]
        
        # If no files match, return None
        if not matching_files:
            print("No matching JSON files found.")
            return None
        
        # If multiple files match, handle it accordingly (e.g., use the first match or process all)
        # Here, we'll assume the first match for simplicity
        json_file = matching_files[0]
        json_file_path = os.path.join(file_path, json_file)

        spark = xursparks.getSparkSession()
        
        sparkdf = spark.read.json(json_file_path)

        return sparkdf
    
    def sheet_name_extractor(self, file_path: str,
                             pattern: str):
        
        # Read the Excel file
        excel_file = pd.ExcelFile(file_path)

        # Get the list of sheet names
        sheet_names = excel_file.sheet_names

        # Loop through the sheet names to find the first match
        for sheet_name in sheet_names:
            if re.match(pattern.lower(), sheet_name.lower()):  # Make the comparison case-insensitive
                return sheet_name

        raise NoMatchingSheetError(f"No matching sheet found for pattern: {pattern}")
    
class NoMatchingSheetError(Exception):
    """Custom exception for no matching sheet found."""
    pass