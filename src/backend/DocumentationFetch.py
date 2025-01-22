from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, udf, parse_json
from snowflake.snowpark.types import StringType
from dotenv import load_dotenv
from pathlib import Path

import os
import json

# Load environment variables
load_dotenv()

# Define Snowflake connection parameters
connection_params = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
}

try:
    # Create a Snowflake session
    session = Session.builder.configs(connection_params).create()
    print("Connected to Snowflake successfully!")

    # Example: Data to be stored in Snowflake
    data = [{"text": "Test", "category": "Test", "value": 2}]

    # Create a dataframe and append data to the existing table
    df = session.create_dataframe(data)
    df.write.mode("append").save_as_table("llm_generated_data")

    # Query data from the Snowflake table
    retrieved_data = session.table("llm_generated_data").collect()
    print("Retrieved data:", retrieved_data)

except Exception as e:
    print(f"An error occurred: {e}")

'''
def saveDocumentation(table_name, data):
    try:
        # Create a Snowflake session
        session = Session.builder.configs(connection_params).create()
        print("Connected to Snowflake successfully!")

        # Example: Data to be stored in Snowflake
        data = [{"text": "Test", "category": "Test", "value": 2}]

        # Create a dataframe and append data to the existing table
        df = session.create_dataframe(data)
        df.write.mode("append").save_as_table(table_name)

        # Query data from the Snowflake table
        retrieved_data = session.table(table_name).collect()
        print("Retrieved data:", retrieved_data)

    except Exception as e:
        print(f"An error occurred: {e}")
'''