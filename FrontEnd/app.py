import json
import os
import mysql.connector
from mysql.connector import Error
from flask import Flask, render_template_string, request
import subprocess  # Used to call external Python scripts

app = Flask(__name__)

# Initialize log messages list
log_messages = []

def connect():
    """Establish and return a connection to the MySQL database using mysql-connector."""
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',  # Change as needed
            port=3306,          # Change as needed
            user='root',        # Change as needed
            password='Mugiwara4521',  # Change as needed
            database='PowerData'  # Change as needed
        )
        if connection.is_connected():
            log("Successfully connected to the MySQL database 'PowerData'.")
            return connection
    except Error as e:
        log(f"Error connecting to the MySQL database: {e}")
        return None

def log(message):
    """Log messages to the log_messages list."""
    log_messages.append(message)

def select_database(connection, db_name):
    """Select the database before executing any SQL commands."""
    try:
        cursor = connection.cursor()
        cursor.execute(f"USE `{db_name}`;")
        log(f"Database selected: {db_name}")
    except Exception as e:
        log(f"Error selecting database: {e}")

def execute_sql_script(connection, sql_file):
    """Execute the SQL script from the given file to create tables."""
    try:
        with open(sql_file, 'r') as file:
            sql_script = file.read()

        cursor = connection.cursor()
        for result in cursor.execute(sql_script, multi=True):
            if result.with_rows:
                log(f"Executed a statement from {sql_file}: {result.statement}")
        log(f"Successfully executed: {sql_file}")
        cursor.close()
    except Exception as e:
        log(f"Error executing {sql_file}: {e}")

def create_tables():
    """Read the sql_file_paths.json and execute each SQL script to create tables."""
    try:
        with open('Assets/jsons/sql_create_queries_file_paths.json', 'r') as json_file:
            sport_sql_files = json.load(json_file)

        connection = connect()

        if connection:
            # Select the PowerData database
            select_database(connection, 'PowerData')
            
            for sport, sql_files in sport_sql_files.items():
                log(f"Creating tables for {sport}...")
                for category, sql_file in sql_files.items():
                    if os.path.exists(sql_file):
                        log(f"Executing {category}: {sql_file}")
                        execute_sql_script(connection, sql_file)
                    else:
                        log(f"SQL file not found: {sql_file}")
            
            connection.close()
        else:
            log("Failed to connect to the database.")
    except Exception as e:
        log(f"Error in create_tables: {e}")

# New function to scrape the entire database
def scrape_entire_database():
    try:
        # Run the external Scraper.py script
        result = subprocess.run(['python', 'Scraper.py'], capture_output=True, text=True)
        log(f"Scrape output: {result.stdout}")
        if result.stderr:
            log(f"Scrape error: {result.stderr}")
    except Exception as e:
        log(f"Error during scraping: {e}")

# New function to drop all tables
def drop_all_tables():
    try:
        # Run the external CleanDatabase.py script
        result = subprocess.run(['python', 'DatabaseUtils/CleanDatabase.py'], capture_output=True, text=True)
        log(f"Drop tables output: {result.stdout}")
        if result.stderr:
            log(f"Drop tables error: {result.stderr}")
    except Exception as e:
        log(f"Error during table drop: {e}")

@app.route('/')
def home():
    return render_template_string(template(), logs=log_messages)

@app.route('/create_database', methods=['POST'])
def create_database():
    db_name = request.form.get('db_name')
    if db_name:
        connection = connect()
        try:
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE `{db_name}`;")
            log(f"Database '{db_name}' created successfully.")
            cursor.close()
        except Error as e:
            log(f"Error creating database '{db_name}': {e}")
        finally:
            connection.close()
    return render_template_string(template(), logs=log_messages)

@app.route('/delete_database', methods=['POST'])
def delete_database():
    db_name = request.form.get('db_name')
    if db_name:
        connection = connect()
        try:
            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE `{db_name}`;")
            log(f"Database '{db_name}' deleted successfully.")
            cursor.close()
        except Error as e:
            log(f"Error deleting database '{db_name}': {e}")
        finally:
            connection.close()
    return render_template_string(template(), logs=log_messages)

# New route to call the scrape function
@app.route('/scrape_database', methods=['POST'])
def scrape_database():
    scrape_entire_database()
    return render_template_string(template(), logs=log_messages)

# New route to call the drop tables function
@app.route('/drop_tables', methods=['POST'])
def drop_tables():
    drop_all_tables()
    return render_template_string(template(), logs=log_messages)

def template():
    """HTML template with CSS for styling."""
    return """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Database Manager</title>
        <style>
            body {
                font-family: 'Arial', 'Helvetica', sans-serif; /* Close alternative to Aptos */
                background-color: #f4f4f4;
                color: #333;
                padding: 20px;
            }
            h1 {
                color: black; /* Keep the Database Manager heading in black */
            }
            form {
                margin-bottom: 20px;
            }
            input[type="text"] {
                padding: 10px;
                width: 200px;
                margin-right: 10px;
                font-family: 'Arial', 'Helvetica', sans-serif; /* Matching form text with body */
            }
            input[type="submit"] {
                padding: 10px 20px;
                background-color: #C00000; /* Updated button color */
                color: white;
                border: none;
                cursor: pointer;
                font-family: 'Arial', 'Helvetica', sans-serif; /* Matching button text with body */
            }
            input[type="submit"]:hover {
                background-color: #A00000; /* Slightly darker red on hover */
            }
            .logs {
                margin-top: 20px;
                background: #fff;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .log-message {
                margin: 5px 0;
                padding: 5px;
                border-left: 5px solid #C00000; /* Updated log message border to match button color */
            }
        </style>
    </head>
    <body>
        <h1>Database Manager</h1>
        <form method="POST" action="/create_database">
            <input type="text" name="db_name" placeholder="Enter Database Name" required>
            <input type="submit" value="Create Database">
        </form>
        <form method="POST" action="/delete_database">
            <input type="text" name="db_name" placeholder="Enter Database Name" required>
            <input type="submit" value="Delete Database">
        </form>
        <form method="POST" action="/scrape_database">
            <input type="submit" value="Scrape Entire Database">
        </form>
        <form method="POST" action="/drop_tables">
            <input type="submit" value="Drop All Tables">
        </form>
        <div class="logs">
            <h2>Log Messages:</h2>
            {% for log in logs %}
                <div class="log-message">{{ log }}</div>
            {% endfor %}
        </div>
    </body>
    </html>
    """



if __name__ == '__main__':
    create_tables()  # Call this before starting the Flask app
    app.run(debug=True)