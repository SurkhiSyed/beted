import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
import base64  # To encode images as base64

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate('../key.json')  # Path to your Firebase Admin SDK private key file
    firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# Initialize session state for authentication
if "auth_state" not in st.session_state:
    st.session_state.auth_state = False  # Default to not logged in

# Sidebar Login/Signup functionality
def authenticate_user():
    st.sidebar.title("BetEd Authentication")

    if st.session_state.auth_state:
        # Display logout button when the user is logged in
        st.sidebar.success("You are logged in!")
        if st.sidebar.button("Logout"):
            st.session_state.auth_state = False  # Set auth state to logged out
            st.session_state.user = None  # Clear the user from session state
            st.sidebar.warning("You have logged out.")
            st.rerun()  # Refresh the app to reflect logout
    else:
        # Display login/signup options when the user is not logged in
        auth_choice = st.sidebar.radio("Login/Sign Up", ["Login", "Sign Up"])

        if auth_choice == "Login":
            email = st.sidebar.text_input("Email Address", key="login_email")
            password = st.sidebar.text_input("Password", type="password", key="login_password")
            if st.sidebar.button("Login"):
                try:
                    user = auth.get_user_by_email(email)
                    st.session_state.auth_state = True  # Set auth state to logged in
                    st.session_state.user = user  # Store the user in session state
                    st.sidebar.success(f"Welcome back, {email}!")
                    st.rerun()  # Refresh the app to show logged-in state
                except auth.UserNotFoundError:
                    st.sidebar.error("Login failed. Please check your credentials.")
                except Exception as e:
                    st.sidebar.error(f"An error occurred: {e}")
        else:
            email = st.sidebar.text_input("Email Address", key="signup_email")
            password = st.sidebar.text_input("Password", type="password", key="signup_password")
            username = st.sidebar.text_input("Enter your unique username", key="signup_username")
            user_level = st.sidebar.radio("User Level", ["Professional", "Regular"], key="user_level")
            profile_picture = st.sidebar.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"], key="profile_picture")
            if st.sidebar.button("Sign Up"):
                try:
                    if profile_picture is None:
                        st.sidebar.error("Please upload a profile picture.")
                        return
                    
                    # Read and encode the uploaded profile picture as a base64 string
                    profile_picture_data = profile_picture.read()
                    profile_picture_base64 = base64.b64encode(profile_picture_data).decode('utf-8')
                    
                    # Create user
                    user = auth.create_user(email=email, password=password)

                    # Save user data, including profile picture, in Firestore
                    db.collection("users").document(user.uid).set({
                        "email": email,
                        "username": username,
                        "user_level": user_level,
                        "profile_picture": profile_picture_base64,
                    })

                    st.sidebar.success("Account created successfully! Please log in.")
                except Exception as e:
                    st.sidebar.error(f"Sign up failed: {e}")
            if user_level == "Professional":
                st.sidebar.write("You have access to all features.")
            else:
                st.sidebar.write("You have limited access to features.")

# Call the authentication function in the sidebar
authenticate_user()

# Example page content
if st.session_state.auth_state:
    st.title("Welcome to BetEd!")
    st.write("You are logged in. Enjoy exploring the platform.")
else:
    st.title("Welcome to BetEd!")
    st.write("Please log in or sign up using the sidebar to access more features.")
