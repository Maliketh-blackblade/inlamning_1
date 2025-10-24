from flask import Flask, render_template, request, session, flash
import mysql.connector
from mysql.connector import Error
import os
import logging
from logging.handlers import RotatingFileHandler
import random as rand

app = Flask(__name__)
app.secret_key = str(rand.randint(1, 1000))
# 'secret_key'  # TODO: Ändra detta till en slumpmässig hemlig nyckel

# Databaskonfiguration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Ändra detta till ditt MySQL-användarnamn
    'password': '',  # Ändra detta till ditt MySQL-lösenord
    'database': 'inlamning_1'  # TODO: Ändra detta till ditt databasnamn
}

def get_db_connection():
    """Skapa och returnera en databasanslutning"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Fel vid anslutning till MySQL: {e}")
        return None
    
def set_up_logging():
    """Set up logging for the application."""
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Create a rotating file handler for logging, keeps the 10 most recent logs
    # removing the oldest when the log file exceeds 10KB
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    
    # sets up the log format (how the log messages will appear in the log file)
    file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    
    # Set the logging level to INFO
    file_handler.setLevel(logging.INFO)

    # Add the handler to the app logger
    app.logger.addHandler(file_handler)

    # Set the overall logging level for the app
    app.logger.setLevel(logging.INFO)

    # Log that the app has started
    app.logger.info('Flask Error Handling Demo startup')


@app.route('/trigger-500')
def trigger_500():
    """Route that intentionally triggers a 500 error by dividing by zero"""
    app.logger.warning('Someone accessed the /trigger-500 route')
    # This will cause a ZeroDivisionError and trigger our 500 error handler
    result = 1 / 0
    return f"This should never be reached: {result}"

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Custom 404 error handler"""
    app.logger.warning(f'404 error: {request.url}')
    
    # it is posible to render a template and return a status code other than 200
    return render_template('errors/404.html'), 404 # 404 is the status code for not found errors

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 error handler"""
    app.logger.error(f'Internal server error: {error}')
    return render_template('errors/500.html'), 500 # 500 is the status code for internal server error

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle any unhandled exceptions"""
    app.logger.error(f'Unhandled exception: {error}', exc_info=True)
    return render_template('errors/500.html'), 500 # 500 is the status code for internal server error


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    # hantera POST request från inloggningsformuläret
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Anslut till databasen
        connection = get_db_connection()
        if connection is None:
            return "Databasanslutning misslyckades", 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            
            if user and user['password'] == password:
                # Inloggning lyckades - spara användarinfo i session
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash (f'Inloggning lyckades! Välkommen {user["username"]}!')
                return render_template('home.html', username=user['username'])
            else:
                # Inloggning misslyckades, skicka http status 401 (Unauthorized)
                flash('Ogiltigt användarnamn eller lösenord')
                return render_template('login.html'), 401

            # # Fråga för att kontrollera om användare finns med matchande användarnamn
            # # TODO: anropa databasen och hämta resultatet med cursor.fetchone() se https://www.geeksforgeeks.org/dbms/querying-data-from-a-database-using-fetchone-and-fetchall/
            # # lägg resultatet i variabeln user nedan.
            # user = # TODO: ska få värdet som är raden i databasen som returneras av query ovan.
            
            # # Kontrollera om användaren fanns i databasen och lösenordet är korrekt.
            # # Om lösenordet är korrekt så sätt sessionsvariabler och skicka tillbaka en hälsning med användarens namn.
            # # Om lösenordet inte är korrekt skicka tillbaka ett felmeddelande med http-status 401.
            # if user ...: # TODO: gör klart villkoret
            #     # Inloggning lyckades - spara användarinfo i session
            #     ... # TODO: spara i sessionen
            #     return f'Inloggning lyckades! Välkommen {...}!'
            # else:
            #     # Inloggning misslyckades, skicka http status 401 (Unauthorized)
            #     return ('Ogiltigt användarnamn eller lösenord', 401)

        except Error as e:
            print(f"Databasfel: {e}")
            return "Databasfel inträffade", 500
        
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

if __name__ == '__main__':
    set_up_logging()
    app.run(debug=True)