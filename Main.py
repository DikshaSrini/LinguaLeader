import streamlit as st
import random
import string
import smtplib
from email.message import EmailMessage
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
import langid  # For language detection

background_color = "#f0f0f0"
button_color = "#008080"
text_color = "#333333"

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    full_name = Column(String)
    email = Column(String)
    is_active = Column(Boolean, default=True)

# Function to apply custom CSS styling
def set_css():
    st.markdown(
        f"""
        <style>
        .reportview-container {{
            background-color: {background_color};
            color: {text_color};
        }}
        .sidebar .sidebar-content {{
            background-color: {background_color};
        }}
        .Widget {{
            color: {text_color};
        }}
        .stButton button {{
            background-color: {button_color};
            color: white;
        }}
        .stTextInput {{
            background-color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to initialize database tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Function to fetch all users from database
def show_users():
    db = next(get_db())
    users = db.query(User).all()
    return users

# Function to register a new user
def register_user(username, password, full_name, email):
    db = next(get_db())
    new_user = User(username=username, password=password, full_name=full_name, email=email)
    db.add(new_user)
    db.commit()

# Function to update user password
def update_password(username, new_password):
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.password = new_password
        db.commit()

# Function to handle OTP generation
def generate_otp():
    otp = ''.join(random.choices(string.digits, k=6))
    return otp

# Function to send OTP via email
def send_otp_email(email, otp):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    from_mail = 'jithuj2003@gmail.com'  
    server.login(from_mail, 'jmyq jnvt uwxy jxof') 
    msg = EmailMessage()
    msg['Subject'] = "OTP Verification"
    msg['From'] = from_mail
    msg['To'] = email
    msg.set_content("Your OTP is: " + otp)
    server.send_message(msg)
    server.quit()

def forgot_password_page():
    st.header("Forgot Password")
    email = st.text_input("Enter your email")

    if st.button("Send OTP"):
        db = next(get_db())
        user = db.query(User).filter(User.email == email).first()
        if user:
            otp = generate_otp()
            send_otp_email(email, otp)

            st.info(f"Password reset instructions sent to {email}")
            st.session_state["reset_email"] = email
            st.session_state["expected_otp"] = otp

            input_otp = st.text_input("Enter OTP received via email", key="input_otp")
            if st.button("Verify OTP"):
                expected_otp = st.session_state.get("expected_otp")
                if input_otp == expected_otp:
                    if len(input_otp) == 6 and input_otp.isdigit():
                        st.success("Valid OTP. Proceed to reset your password.")
                        st.empty()
                        reset_password_page(user.username)
                    else:
                        st.error("Invalid OTP. Please enter a 6-digit numeric code.")
                else:
                    st.error("Invalid OTP. Please try again.")
        else:
            st.error("Email address not found in our records.")

def reset_password_page(username):
    st.header("Reset Password")

    with st.form("reset_password_form"):
        new_password = st.text_input("Enter new password", type="password")
        confirm_new_password = st.text_input("Confirm new password", type="password")
        submit_button = st.form_submit_button("Reset Password")

        if submit_button:
            if new_password == confirm_new_password:
                update_password(username, new_password)
                st.success("Password reset successful.")
                st.info("You can now proceed to login with your new password.")
                if st.button("Go to Login Page"):
                    st.experimental_rerun()
            else:
                st.error("Passwords do not match.")

        if st.session_state.get("expected_otp"):
            st.write("Already verified OTP? Re-enter your new password below:")
            reenter_new_password = st.text_input("Re-enter new password", type="password")
            update_button = st.button("Update Password")
            if update_button:
                if new_password == reenter_new_password:
                    update_password(username, new_password)
                    st.success("Password updated successfully.")
                    st.info("You can now proceed to login with your new password.")
                    if st.button("Go to Login Page"):
                        st.experimental_rerun()
                else:
                    st.error("Passwords do not match.")

def new_login_page():
    st.header("New Login")

    with st.form("new_login_form"):
        new_password = st.text_input("Enter new password", type="password")
        confirm_new_password = st.text_input("Confirm new password", type="password")
        submit_button = st.form_submit_button("Set New Password")

        if submit_button:
            if new_password == confirm_new_password:
                username = st.text_input("Username")
                update_password(username, new_password)
                st.success("Password set successfully.")
                st.info("You can now proceed to login with your new password.")
                if st.button("Go to Login Page"):
                    st.experimental_rerun()
            else:
                st.error("Passwords do not match.")

def login_page():
    st.header("Login Page")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        db = next(get_db())
        user = db.query(User).filter(User.username == username, User.password == password).first()
        if user:
            st.success(f"Logged in as: {username}")
            st.info("You can now access your account.")
        else:
            st.error("Invalid username or password")

    if st.session_state.get("forgot_password", False):
        forgot_password_page()
    elif st.button("Forgot Password?"):
        st.session_state["forgot_password"] = True

def register_page():
    st.header("Register Page")
    username_new = st.text_input("New Username")
    password_new = st.text_input("New Password", type="password")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")

    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Register"):
        if password_new == confirm_password:
            try:
                register_user(username_new, password_new, full_name, email)
                st.success(f"Registration successful for: {username_new}")
            except OperationalError as e:
                st.error(f"Error: {str(e)}")
        else:
            st.error("Passwords do not match")

# Language prediction functionality
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "zh": "Chinese",
    "ja": "Japanese",
    "ru": "Russian",
    "ar": "Arabic",
    "pt": "Portuguese",
    "it": "Italian",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "kn": "Kannada",
    "gu": "Gujarati",
    "mr": "Marathi",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu",
    "as": "Assamese",
    "ne": "Nepali",
    "sd": "Sindhi",
    "si": "Sinhalese",
    "bh": "Bhojpuri",
    "br": "Braj",
    "ks": "Kashmiri",
    "mk": "Maithili",
    "ko": "Korean",

}

def language_prediction_page():
    st.header("Language Prediction")
    text_input = st.text_area("Enter text to predict the language:")
    
    if st.button("Predict"):
        if text_input:
            lang_code, _ = langid.classify(text_input)
            lang_name = LANGUAGE_MAP.get(lang_code, "Unknown Language")
            st.success(f"Predicted Language: {lang_name} ({lang_code})")
        else:
            st.error("Please enter some text for prediction.")

def main():
    set_css()
    create_tables()

    st.title("Streamlit Application")

    # Navigation
    page = st.sidebar.selectbox("Select a page", ["Home", "Login", "Register", "Forgot Password", "New Login", "Show Users", "Language Prediction"])

    if page == "Home":
        st.header("Home Page")
        st.write("Welcome to our application!")
        st.write("Please log in or register to continue.")
        st.markdown("[Go to Login Page](#Login)")
        st.markdown("[Go to Register Page](#Register)")

    elif page == "Login":
        login_page()

    elif page == "Register":
        register_page()

    elif page == "Forgot Password":
        forgot_password_page()

    elif page == "New Login":
        new_login_page()

    elif page == "Show Users":
        st.header("Users in Database")
        users = show_users()
        if users:
            for user in users:
                st.write(f"Username: {user.username}, Full Name: {user.full_name}, Email: {user.email}")
        else:
            st.write("No users found in the database.")

    elif page == "Language Prediction":
        language_prediction_page()

if __name__ == "__main__":
    main()


