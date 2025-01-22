import requests
from snowflake.snowpark import Session
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse

load_dotenv()

connection_params = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
}


def fetch_hackathon_links():
    try:
        api_key = os.getenv("YOUR_GOOGLE_API_KEY")
        cx = "534e24bde2cf04ce0"
        url = f"https://www.googleapis.com/customsearch/v1?q=Devpost+upcoming+hackathons&key={api_key}&cx={cx}"

        response = requests.get(url)
        response.raise_for_status()
        results = response.json()

        links = [item['link'] for item in results.get('items', [])]
        return links
    except Exception as e:
        print(f"Error fetching hackathon links: {e}")
        return []


def fetch_hackathon_details(link):
    try:
        response = requests.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('h1').get_text(strip=True) if soup.find('h1') else "N/A"
        date = soup.find('span', class_='event-date').get_text(strip=True) if soup.find('span', class_='event-date') else "N/A"
        about = soup.find('div', class_='about-section').get_text(strip=True) if soup.find('div', class_='about-section') else "N/A"

        return {
            "name": name,
            "date": date,
            "about": about,
            "link": link
        }
    except Exception as e:
        print(f"Error fetching details from {link}: {e}")
        return None


def store_hackathons_in_snowflake(hackathon_data, table_name):
    try:
        session = Session.builder.configs(connection_params).create()
        print("Connected to Snowflake successfully!")

        database_name = "HACKATHONS"
        schema_name = connection_params["schema"]

        # Create table dynamically
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {database_name}.{schema_name}.{table_name} (
            name STRING,
            date STRING,
            about STRING,
            link STRING
        );
        """
        session.sql(create_table_query).collect()
        print(f"Ensured table {table_name} exists in schema {schema_name} of database {database_name}.")

        # Insert data into the table
        df = session.create_dataframe(hackathon_data)
        df.write.mode("append").save_as_table(f"{database_name}.{schema_name}.{table_name}")
        print(f"Stored hackathon data in table {table_name}.")
    except Exception as e:
        print(f"Error storing hackathon data in Snowflake: {e}")


def main_function():
    try:
        print("Fetching hackathon links...")
        hackathon_links = fetch_hackathon_links()

        if not hackathon_links:
            print("No hackathon links found.")
            return

        print(f"Found {len(hackathon_links)} hackathon links. Fetching details...")

        for link in hackathon_links:
            print(f"Fetching details for {link}...")
            details = fetch_hackathon_details(link)

            if details:
                # Generate a table name from the website's domain
                domain = urlparse(link).netloc.replace('.', '_').lower()
                table_name = f"hackathons_{domain}"

                # Store details in Snowflake
                store_hackathons_in_snowflake([details], table_name)
    except Exception as e:
        print(f"Error in main function: {e}")


if __name__ == "__main__":
    main_function()
