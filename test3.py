import streamlit as st
import pandas as pd
import hashlib
import mysql.connector
from mysql.connector import Error
import webbrowser
from transformers import BartForConditionalGeneration, BartTokenizer
import torch
import time
import json
from datetime import datetime, timedelta
import os
import re
from streamlit_option_menu import option_menu

# Convert password to hash format
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Check if hashed passwords match
def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# DB Management
def create_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',      # e.g., 'localhost' or the IP address of the MySQL server
            user='root',           # your MySQL username
            password='6364560426', # your MySQL password
            database='sharuk'      # name of the database you want to connect to
        )
        if conn.is_connected():
            return conn
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

# DB Functions for create table
def create_usertable(conn):
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS userstable (username VARCHAR(255), email VARCHAR(255), password TEXT)')
    conn.commit()

# Insert the data into table
def add_userdata(conn, username, email, password):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO userstable (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
    conn.commit()

# Password and email fetch
def login_user(conn, email):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM userstable WHERE email = %s', (email,))
    data = cursor.fetchone()
    return data

# Update password
def update_password(conn, email, new_password):
    cursor = conn.cursor()
    hashed_password = make_hashes(new_password)
    cursor.execute('UPDATE userstable SET password = %s WHERE email = %s', (hashed_password, email))
    conn.commit()

def view_all_users(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM userstable')
    data = cursor.fetchall()
    return data

# Summarization Tool Page
def summarization_tool():    
    st.markdown('<div class="box"><h2>Summarization Tool</h2></div>', unsafe_allow_html=True)
    # Example summarization tool code
    model_path = '/Users/mohammedroshan/Downloads/summarizrtion/fine_tuned_bart1'
    model = BartForConditionalGeneration.from_pretrained(model_path)
    tokenizer = BartTokenizer.from_pretrained('/Users/mohammedroshan/Downloads/summarizrtion/tokenizer1')
    text = st.text_area("Enter text to summarize")
    
    # Load history for the current user
    def load_history():
        history_file = f'{st.session_state.username}_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
        else:
            return []
    
    # Save history for the current user
    def save_history(history):
        history_file = f'{st.session_state.username}_history.json'
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
            
    # Categorize history entries
    def categorize_history(history):
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        today_entries = []
        yesterday_entries = []
        previous_entries = []

        for entry in history:
            entry_date = datetime.fromisoformat(entry['timestamp']).date()
            if entry_date == today:
                today_entries.append(entry)
            elif entry_date == yesterday:
                yesterday_entries.append(entry)
            else:
                previous_entries.append(entry)

        return today_entries, yesterday_entries, previous_entries
    
    st.sidebar.title('History')
    history = load_history()
    today_entries, yesterday_entries, previous_entries = categorize_history(history)
    if today_entries:
        with st.sidebar.expander("Today"):
            for i, entry in enumerate(today_entries):
                st.write(f"**Original:** {entry['text']}")
                st.write(f"**Summary:** {entry['summary']}")

    if yesterday_entries:
        with st.sidebar.expander("Yesterday"):
            for i, entry in enumerate(yesterday_entries):
                st.write(f"**Original:** {entry['text']}")
                st.write(f"**Summary:** {entry['summary']}")

    if previous_entries:
        with st.sidebar.expander("Previous Days"):
            for i, entry in enumerate(previous_entries):
                st.write(f"**Original:** {entry['text']}")
                st.write(f"**Summary:** {entry['summary']}")   
    
    
    
    if st.button("Summarize"):
        if text:
            inputs = tokenizer(text, max_length=1024, truncation=True, return_tensors='pt')
        
            # Generate summary
            summary_ids = model.generate(inputs['input_ids'], max_length=500, min_length=100, num_beams=4, early_stopping=True)
            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            st.subheader("Summary")
            def stream():
                for word in summary.split(" "):
                    yield word + " "
                    time.sleep(0.05)
                
            st.write_stream(stream)
            
            #st.text_area("Summary", summary, height=150)
            
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'text': text,
                'summary': summary
            }
                    
            history.append(history_entry)

            # Save history
            save_history(history)

            # Refresh the page to update the sidebar
            #st.experimental_rerun()
        else:
            st.write("Please enter some text to summarize.")              
    
# Main function
def main():
    st.markdown("""
        <style>
            .main {
                background: #71797E;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
                color: white;
            }
            .sidebar .sidebar-content {
                background: #FFCC44;
                color: white;
            }
            .title h1 {
                color: #36454F;
                text-align: center;
            }
            .box {
                background: #A9A9A9;
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
                
            }
            .stButton{
                justify-content: center;
                align-items: center;
            }
            .stButton button {
                background: #B2BEB5;
                color: white;
                border: none;
                padding: 20px;
                border-radius: 5px;
                width: 700px;
                height: 20px;
                justify-content: center;
                align-items: center;
                margin: 5px;
                cursor: pointer;
            }
            .stButton button:hover {
                background: #B2BEB5;
            }
            .dataframe {
                border: 1px solid #ddd;
                border-radius: 10px;
                overflow: hidden;
            }
            .sidebar .sidebar-content a {
                color: #b0b3b8;
                text-decoration: none;
                padding: 10px;
                display: block;
                border-radius: 5px;
            }
            .sidebar .sidebar-content a:hover {
                background: #CACBCE;
                color: white;
            }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="title"><h1>Welcome!</h1></div>', unsafe_allow_html=True)
    
    conn = create_connection()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.email = ""
        st.session_state.menu = 'Login'
        st.session_state.email_for_reset = None
    
    if st.session_state.logged_in:
        summarization_tool()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.email = ""
            st.session_state.menu = 'Login'
            st.rerun()

    else:
        with st.sidebar:
            menu = option_menu("Navigation", 
                           ["Login", "Create Account", "Forgot Password?", "Reset Password"],
                           icons=['person', 'person-plus', 'question-circle', 'key'], 
                           menu_icon="menu-app",
                           default_index=["Login", "Create Account", "Forgot Password?", "Reset Password"].index(st.session_state.menu))
        
        if menu == "Login":
            st.markdown('<div class="box"><h2>Log in to the App</h2></div>', unsafe_allow_html=True)
            email = st.text_input("Email", placeholder='Your unique email')
            password = st.text_input("Password", placeholder='Your password', type='password')
            
            if st.button("Login"):
                create_usertable(conn)
                user_data = login_user(conn, email)
                
                if user_data:
                    stored_username, stored_email, stored_password = user_data
                    if check_hashes(password, stored_password):
                        st.success("Login successful")
                        st.session_state.logged_in = True
                        st.session_state.username = stored_username
                        st.session_state.email = stored_email
                        st.session_state.menu = 'Login'
                        st.rerun()
                    else:
                        st.error("Incorrect password")
                else:
                    st.error("User not found")
                    
        elif menu == "Create Account":
            st.markdown('<div class="box"><h2>Create an Account</h2></div>', unsafe_allow_html=True)
            new_user = st.text_input("Username", placeholder='Your unique username')
            new_email = st.text_input('Email id', placeholder='Your email')
            new_password = st.text_input("Password", placeholder='Your password', type='password')
            confirm_password = st.text_input("Confirm Password",placeholder='Confirm your new password', type='password')
            
            def validate_email(email):
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                return re.match(email_pattern, email) is not None

            def validate_password(password):
                password_pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
                return re.match(password_pattern, password) is not None
            
            if st.button("Create Account"):
                if not validate_email(new_email):
                    st.warning("Enter the correct email pattern")
                elif not validate_password(new_password):
                    st.warning("The password must contain one special character one number and one capital letter")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    create_usertable(conn)
                    hashed_password = make_hashes(new_password)
                    add_userdata(conn, new_user, new_email, hashed_password)
                    st.success("Account created successfully")
                    st.info("Go to Login to access your account")
                    
        elif menu == "Forgot Password?":
            st.markdown('<div class="box"><h2>Forgot Password</h2></div>', unsafe_allow_html=True)
            st.session_state.email_for_reset = st.text_input("Email", placeholder='Your unique email')
            
            if st.button("Submit"):
                user_data = login_user(conn, st.session_state.email_for_reset)
                if user_data:
                    st.session_state.menu = "Reset Password"
                    st.rerun()
                else:
                    st.error("User not found")
                    
        elif menu == "Reset Password":
            st.markdown('<div class="box"><h2>Reset Password</h2></div>', unsafe_allow_html=True)
            if st.session_state.email_for_reset:
                new_password = st.text_input("New Password",placeholder='your new password', type='password')
                confirm_password = st.text_input("Confirm Password",placeholder='Confirm your new password', type='password')
                
                def validate_password(password):
                    password_pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
                    return re.match(password_pattern, password) is not None
                
                if st.button("Reset Password"):
                    if not validate_password(new_password):
                        st.warning("The password must contain one special character one number and one capital letter")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")   
                    else:
                        update_password(conn, st.session_state.email_for_reset, new_password)
                        st.success("Password reset successful")
                        st.session_state.menu = "Login"
                        st.rerun()
            else:
                st.error("Invalid access. Please go to Forgot Password and submit your email.")
    
if __name__ == '__main__':
    main()
