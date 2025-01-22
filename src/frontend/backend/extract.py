import requests
from snowflake.snowpark import Session
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import os

load_dotenv()

connection_params = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
}

def fetch_documentation_link(query):
    """
    Fetches the official documentation link for a given framework using Google's Custom Search API.
    """
    try:
        api_key = os.getenv("YOUR_GOOGLE_API_KEY")
        cx = "534e24bde2cf04ce0"  
        url = f"https://www.googleapis.com/customsearch/v1?q={query}+official+documentation&key={api_key}&cx={cx}"
        
        response = requests.get(url)
        results = response.json()
        return results['items'][0]['link'] if 'items' in results else None
    except Exception as e:
        print(f"Error fetching base link for {query}: {e}")
        return None

def get_subpage_links(base_url):
    """
    Extracts all documentation links, including cross-references to other pages, from the base URL.
    """
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse all links on the page
            links = set()
            base_domain = '/'.join(base_url.split('/')[:3])  # Extracts domain from the base URL
            
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.startswith('http'):  # Full external link
                    if base_domain in href:  # Keep links within the same domain
                        links.add(href)
                elif href.startswith('/'):  # Relative internal link
                    links.add(base_domain + href)
                elif not href.startswith('javascript'):  # Handle edge cases
                    links.add(base_url.rstrip('/') + '/' + href)
            
            return links
        else:
            print(f"Failed to fetch subpage links from {base_url}")
            return set()
    except Exception as e:
        print(f"Error fetching subpage links: {e}")
        return set()


def fetch_documentation(link):
    """
    Fetch and extract clean text content from the documentation page.
    Excludes div tags and code blocks.
    """
    try:
        response = requests.get(link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted elements like code blocks
            for code_block in soup.find_all(['code', 'pre']):
                code_block.decompose()  # Remove from the soup

            text_content = soup.get_text(separator='\n', strip=True)
            return text_content
        else:
            print(f"Failed to fetch documentation from {link}")
            return None
    except Exception as e:
        print(f"Error fetching documentation: {e}")
        return None

def store_documentation(tech, subpage_data):
    try:
        session = Session.builder.configs(connection_params).create()
        print("Connected to Snowflake successfully!")

        # Database, schema, and table names
        database_name = connection_params["database"]
        schema_name = connection_params["schema"]
        table_name = f"{tech}_Documentation"

        # Check if the schema exists
        check_schema_query = f"SHOW SCHEMAS LIKE '{schema_name}' IN DATABASE {database_name}"
        schema_exists = session.sql(check_schema_query).collect()
        if not schema_exists:
            # Create the schema if it doesn't exist
            create_schema_query = f"CREATE SCHEMA {database_name}.{schema_name}"
            session.sql(create_schema_query).collect()
            print(f"Created schema {schema_name} in database {database_name}.")

        # Check if the table exists
        check_table_query = f"SHOW TABLES LIKE '{table_name}' IN SCHEMA {database_name}.{schema_name}"
        table_exists = session.sql(check_table_query).collect()
        if not table_exists:
            # Create the table if it doesn't exist
            create_table_query = f"""
            CREATE TABLE {database_name}.{schema_name}.{table_name} (
                framework STRING,
                subpage STRING,
                content STRING
            );
            """
            session.sql(create_table_query).collect()
            print(f"Created table {table_name} in schema {schema_name} of database {database_name}.")

        # Prepare and store data
        data = [{"framework": tech, "subpage": subpage, "content": content}
                for subpage, content in subpage_data.items()]
        df = session.create_dataframe(data)

        # Append data to the table
        df.write.mode("append").save_as_table(f"{database_name}.{schema_name}.{table_name}")
        print(f"Stored documentation for {tech} in table {table_name}.")
    except Exception as e:
        print(f"An error occurred while storing documentation: {e}")



def main_function(frameworks):
    """
    Fetches the base link for each framework, retrieves all subpages, and stores the documentation.
    """
    for framework in frameworks:
        try:
            print(f"Processing {framework}...")

            base_url = fetch_documentation_link(framework)
            if not base_url:
                print(f"Could not retrieve base URL for {framework}")
                continue
            
            print(f"Base URL for {framework}: {base_url}")

            subpage_links = get_subpage_links(base_url)
            print(f"Found {len(subpage_links)} subpages for {framework}.")

            # Fetch content from each subpage
            subpage_data = {}
            for link in subpage_links:
                print(f"Fetching content from {link}...")
                content = fetch_documentation(link)
                if content:  # Only include pages with valid content
                    subpage_name = link.split('/')[-1] or 'index'
                    subpage_data[subpage_name] = content
                else:
                    print(f"Skipping {link} due to fetch failure.")

            #print(subpage_data)
            # Store in Snowflake if any data was successfully fetched
            if subpage_data:
                store_documentation(framework, subpage_data)
            else:
                print(f"No valid content fetched for {framework}. Skipping storage.")
        except Exception as e:
            print(f"Error processing {framework}: {e}")

#frameworks = ["React.js","Vue.js","Angular","Django","Flask"]
#fetch_and_store_all_documentation(frameworks)
