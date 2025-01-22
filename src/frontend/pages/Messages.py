import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
import streamlit.components.v1 as components


tailwind_css = """
<head>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
"""
components.html(tailwind_css, height=0)
# Add the Tailwind CSS to the Streamlit app


# Firebase initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("../key.json")  # Path to your Firebase key
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()

# Session state for user authentication
def get_user():
    return st.session_state.get('user')

# Function to send a message to Firestore
def send_message(user, message):
    # Send the message to Firestore first
    chat_ref = db.collection("chats")
    chat_ref.add({
        "user_id": user.uid,
        "user_name": user.email,  # or any other field like 'username'
        "message": message,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

# Function to display messages from Firestore
def display_messages():
    chat_ref = db.collection("chats").order_by("timestamp")
    messages = chat_ref.stream()

    for msg in messages:
        message_data = msg.to_dict()
        message_html = f"""
        <html>
            <head>
                <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            </head>
            <body class="h-screen flex items-start justify-start">
                
        """
        if message_data["user_id"] == get_user().uid:
            message_html += f"""
            <div class="bg-blue-400 text-white p-3 rounded-xl mt-0 max-w-md sm:max-w-lg md:max-w-xl lg:max-w-2xl xl:max-w-4xl ml-auto">
                {message_data["user_name"]}: {message_data["message"]}
            </div>
            """
        else:
            message_html += f"""
            <div class="bg-gray-800 text-white p-4 rounded-xl mt-4 max-w-md sm:max-w-lg md:max-w-xl lg:max-w-2xl xl:max-w-4xl mr-auto">
                {message_data["user_name"]}: {message_data["message"]}
            </div>
            """
        
        message_html += "</body></html>"
        components.html(message_html, height=100)
        
# Main Chat Interface
def chat_interface():
    user = get_user()

    if not user:
        st.warning("You need to log in to send messages.")
        return

    
   
    display_messages()
    st.header("Global Chat")
    message = st.text_area("Enter your message:")

    if st.button("Send"):
        if message:
            send_message(user, message)
            st.success("Message sent!")
        else:
            st.warning("Please enter a message.")



# Main execution
if __name__ == "__main__":

    from pages.Login import authenticate_user
    authenticate_user()

    if st.session_state.auth_state and st.session_state.user:
        chat_interface()
    else:
        st.warning("Please log in to access the chat.")
        st.stop()
