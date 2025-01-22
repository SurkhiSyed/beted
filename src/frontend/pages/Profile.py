import streamlit as st
from firebase_admin import firestore
from pages.Login import authenticate_user
import base64  # To decode the base64 image

# Authenticate user
authenticate_user()

# Check if the user is authenticated
if "auth_state" in st.session_state and st.session_state.auth_state:    
    # Access Firestore
    db = firestore.client()

    # Fetch user data
    user_id = st.session_state.user.uid  # Assuming the user's UID is stored in session state
    user_doc = db.collection("users").document(user_id).get()
    col1, col2 = st.columns([3, 7])  # Adjust ratios for sidebar layout

    if user_doc.exists:
        user_data = user_doc.to_dict()
        username = user_data.get("username", "Unknown User")
        email = user_data.get("email", "No Email Provided")
        profile_picture_base64 = user_data.get("profile_picture", None)

        with col2:
            # Display user details
            st.header(f"{username}")
            st.write(f"Email: {email}")
            st.write("Welcome to your profile page!")

            
        with col1:
            # Display profile picture if available
            if profile_picture_base64:
                # Decode base64 string into an image
                profile_picture_bytes = base64.b64decode(profile_picture_base64)
                st.image(profile_picture_bytes, use_container_width=True)
            else:
                st.info("No profile picture uploaded.")
                
    
        st.subheader("Your Stats")

    else:
        st.error("User data not found in the database.")
else:
    st.warning("You need to log in to access this page.")
    st.stop()
