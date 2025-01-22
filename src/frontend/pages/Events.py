import streamlit as st
from pages.Login import authenticate_user
from snowflake.snowpark import Session
import os

# Authenticate user
authenticate_user()

# Snowflake connection parameters
connection_params = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
}

# Fetch data from Snowflake
def fetch_data_from_snowflake():
    try:
        session = Session.builder.configs(connection_params).create()
        print("Connected to Snowflake successfully!")

        database_name = "HACKATHONS"
        schema_name = connection_params["schema"]

        # Query to get all table names in the schema
        table_query = f"SHOW TABLES IN SCHEMA {database_name}.{schema_name}"
        tables = session.sql(table_query).collect()

        hackathon_data = []
        for table in tables:
            table_name = table["name"]

            # Fetch data from each table
            query = f"SELECT * FROM {database_name}.{schema_name}.{table_name}"
            results = session.sql(query).collect()

            # Add data with table name for reference
            for row in results:
                hackathon_data.append({
                    "name": row["NAME"],
                    "date": row["DATE"],
                    "about": row["ABOUT"],
                    "link": row["LINK"],
                })
        
        return hackathon_data
    except Exception as e:
        st.error(f"Error fetching data from Snowflake: {e}")
        return []

# Main content
if "auth_state" in st.session_state and st.session_state.auth_state:
    st.title('Events')
    st.write("Welcome to the events page!")

    # Sidebar for language/framework selection
    col1, col2 = st.columns([7, 3])  # Adjust ratios for layout
    
    with col2:
        st.markdown("### Select Languages or Frameworks:")
        options = [
            "ReactJS",
            "Flask",
            "Django",
            "Vue.js",
            "Angular",
            "ExpressJS",
            "TailwindCSS",
            "Numpy",
            "Pandas",
            "TensorFlow",
            "PyTorch",
            "Pygame",
            "Firebase",
            "GoLang",
            "Other"
        ]

        selected_options = [option for option in options if st.checkbox(option)]
        user_input = st.text_input("Enter a technology:", key="tech_input")

        # Fetch and display data button
        if st.button("Fetch Events"):
            if selected_options or user_input:
                hackathon_data = fetch_data_from_snowflake()
                if hackathon_data:
                    st.success("Data fetched successfully!")
                else:
                    st.warning("No data found.")
            else:
                st.warning("Please select at least one technology or enter an input.")

    with col1:
        st.markdown("### Hackathon Events")
        hackathon_data = fetch_data_from_snowflake()
        if hackathon_data:
            for hackathon in hackathon_data:
                with st.container():
                    st.subheader(hackathon["name"])
                    st.write(f"**Date**: {hackathon['date']}")
                    st.write(f"**About**: {hackathon['about']}")
                    st.markdown(f"[Learn More]({hackathon['link']})")
                    st.markdown("---")  # Separator for cards
        else:
            st.info("No events to display. Please fetch data.")
else:
    st.warning("You need to log in to access this page.")
    st.stop()
