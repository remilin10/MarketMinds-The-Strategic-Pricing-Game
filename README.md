# MarketMinds-The-Strategic-Pricing-Game


This is a Flask web application that simulates an economic game where two users compete to maximize their profits by setting prices over multiple rounds. The application uses real-time updates to notify users when a CSV file has been modified, and it generates plots to visualize demand, profit, and price comparisons over the rounds.

# Features
User authentication and role selection
Real-time notifications of file updates using Flask-SocketIO and Watchdog
Dynamic plotting of demand, profit, and price comparisons using Matplotlib
Storage of game data in CSV files
Simple and intuitive web interface for user interaction

# Requirements
Python 3.7+
Flask
Flask-SocketIO
Watchdog
Matplotlib


# Installation
1. Clone the repository:
   git clone https://github.com/remilin10/MarketMinds-The-Strategic-Pricing-Game
.git
   cd flask-demand-profit-game

2. Create a virtual environment and activate it:
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. Install the dependencies:
   pip install -r requirements.txt
   
5. Create the necessary directories:
   mkdir group_data
   
# Usage
1. Run the Flask application by typing the following in the terminal:
python exp1.py
2. Open your web browser and go to the URL displayed in the terminal for (example: http://0.0.0.0:5000).

3. Select your user role (User 1 or User 2) when prompted.

4. Set your price for each round and submit it.

5. View the results, including demand, profit, and price comparisons for the current and previous rounds.

# File Structure
exp1.py: The main Flask application file.
templates/: Contains the HTML templates for the web pages.
index.html: The main page where users set their prices.
results.html: Displays the results for each round, including plots.
completion.html: Displays a message when the game is completed.
group_data/: Directory where the CSV files storing game data are saved.


# Acknowledgments
Flask documentation: https://flask.palletsprojects.com/
Flask-SocketIO documentation: https://flask-socketio.readthedocs.io/
Watchdog documentation: https://python-watchdog.readthedocs.io/
Matplotlib documentation: https://matplotlib.org/stable/contents.html
   
