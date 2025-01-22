import streamlit as st
import snowflake.connector
from dotenv import load_dotenv
import os
from mistralai import Mistral

# Load environment variables
load_dotenv()

# Snowflake connection parameters
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")

# List of documentation tables with their common names and aliases
FRAMEWORK_MAPPING = {
    "FRAMEWORK_DOCUMENTATION2": ["framework", "frameworks"],
    "ANGULAR_DOCUMENTATION": ["angular", "ng", "angular.js", "angularjs"],
    "BS4_DOCUMENTATION": ["beautiful soup", "bs4", "beautifulsoup", "beautifulsoup4"],
    "DJANGO_DOCUMENTATION": ["django", "django framework"],
    "EXPRESSJS_DOCUMENTATION": ["express", "expressjs", "express.js", "node express"],
    "FIREBASE_DOCUMENTATION": ["firebase", "google firebase"],
    "GOLANG_DOCUMENTATION": ["go", "golang"],
    "JAVA_DOCUMENTATION": ["java", "java programming"],
    "MONGODB_DOCUMENTATION": ["mongodb", "mongo", "mongo db"],
    "NUMPY_DOCUMENTATION": ["numpy", "np"],
    "PANDAS_DOCUMENTATION": ["pandas", "pd"],
    "PYGAME_DOCUMENTATION": ["pygame"],
    "PYTORCH_DOCUMENTATION": ["pytorch", "torch"],
    "REACTJS_DOCUMENTATION": ["react", "reactjs", "react.js"],
    "TAILWINDCSS_DOCUMENTATION": ["tailwind", "tailwindcss", "tailwind css"],
    "TENSORFLOW_DOCUMENTATION": ["tensorflow", "tf"]
}

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

@st.cache_resource
def init_mistral():
    try:
        return Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    except Exception as e:
        st.error(f"Error initializing Mistral client: {e}")
        return None

def detect_frameworks(query):
    """Detect which frameworks are mentioned in the query."""
    query_lower = query.lower()
    relevant_tables = []
    
    for table, aliases in FRAMEWORK_MAPPING.items():
        if any(alias in query_lower for alias in aliases):
            relevant_tables.append(table)
    
    if not relevant_tables:
        return list(FRAMEWORK_MAPPING.keys())
    
    return relevant_tables

def get_snowflake_connection():
    try:
        return snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA
        )
    except Exception as e:
        st.error(f"Failed to connect to Snowflake: {e}")
        return None

def search_documents(query, selected_frameworks=None):
    conn = None
    try:
        conn = get_snowflake_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        
        # Determine which frameworks to search
        relevant_tables = detect_frameworks(query)
        if selected_frameworks:
            selected_tables = [f"{f}_DOCUMENTATION".replace('2', '') for f in selected_frameworks]
            relevant_tables = [t for t in relevant_tables if t in selected_tables]
        
        if not relevant_tables:
            st.warning("No relevant framework detected in the query.")
            return []
        
        # Split query into words for better matching
        query_words = query.lower().split()
        
        # Build query for relevant tables only
        queries = []
        params = []
        for table in relevant_tables:
            # Select all columns from the table
            query_conditions = []
            for word in query_words:
                query_conditions.append(f"LOWER(content) ILIKE %s")
                params.append(f'%{word}%')
            
            conditions = " OR ".join(query_conditions)
            
            queries.append(f"""
                SELECT 
                    *,
                    '{table}' as source_table,
                    COUNT(*) OVER (PARTITION BY '{table}') as match_count
                FROM {table}
                WHERE {conditions}
            """)
        
        full_query = " UNION ALL ".join(queries)
        full_query += " ORDER BY match_count DESC LIMIT 5"
        
        cursor.execute(full_query, params)
        results = cursor.fetchall()
        
        if not results:
            st.warning(f"No results found in the selected frameworks: {', '.join(relevant_tables)}")
        
        return results
        
    except Exception as e:
        st.error(f"Error querying Snowflake: {e}")
        return []
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if conn:
            conn.close()

def generate_answer(query, selected_frameworks=None):
    if not mistral_client:
        return "Mistral client failed to initialize. Please check your API key."

    try:
        # Search for relevant documents
        documents = search_documents(query, selected_frameworks)
        
        if documents:
            # Format context with all available information
            context_parts = []
            st.subheader("Relevant Documentation Found:")
            for doc in documents:
                # Get the source table name from the second-to-last column
                source_table = doc[-2]
                # Use all columns except the last two (source_table and match_count)
                content = " | ".join(str(field) for field in doc[:-2])
                framework_name = source_table.replace('_DOCUMENTATION', '').replace('2', '')
                #st.info(f"Found relevant information in {framework_name}")
                context_parts.append(f"From {framework_name} documentation:\n{content}")
            
            context = "\n\n".join(context_parts)
        else:
            context = "No specific documentation found for this query."
        
        messages = [
            {"role": "system", "content": f"""You are a helpful programming assistant. Use the provided documentation context to answer questions accurately. 
             If the answer cannot be derived from the context, say so. The user's question is about: {query}"""},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}\n\nPlease provide a clear and concise answer based on the context above."}
        ]
        
        response = mistral_client.chat.complete(
            model="mistral-small-latest",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
            top_p=0.95,
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "Failed to generate response."

# Initialize Mistral client
mistral_client = init_mistral()

# Streamlit UI
st.title("Documentation Assistant")
st.markdown("Ask questions about various frameworks and technologies!")

# Chat interface
st.subheader("Chat History")
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.write("You: " + message["content"])
    else:
        st.write("Assistant: " + message["content"])
    st.write(" ")

# Input for user query
user_query = st.text_input("Ask a question about any framework:")
# Framework filter
selected_frameworks = st.multiselect(
    "Filter by framework (optional):",
    options=[table.replace('_DOCUMENTATION', '').replace('2', '') for table in FRAMEWORK_MAPPING.keys()]
)

if user_query:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    with st.spinner("Searching documentation and generating response..."):
        answer = generate_answer(user_query, selected_frameworks)
        # Add assistant response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        
        # Display the latest response
        st.subheader("Latest Answer:")
        st.write(answer)

# Clear chat history button
if st.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.experimental_rerun()
