from flask import Flask, render_template, session, request, redirect, url_for, flash, jsonify
import os
import csv
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import io
import base64
import threading
from flask_socketio import SocketIO, emit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Create a thread pool with a maximum of 10 threads
executor = ThreadPoolExecutor(max_workers=10)


# Constants for economic calculations (if any)
COST = 2
a = 14
d = 0.00333333333333
beta = 0.00666666666666


# Ensure the data directory exists
os.makedirs('group_data', exist_ok=True)

class FileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.csv'):
            socketio.emit('file_updated', {'message': 'File has been updated'})


def start_file_monitor():
    path = 'group_data'
    event_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            socketio.sleep(1)
    finally:
        observer.stop()
        observer.join()

def demand_function(a, d, beta, self_price, rival_price):
    """Calculate the demand based on provided economic formulas."""
    return 1 / (beta * beta - d * d) * ((a * beta - a * d) - beta * self_price + d * rival_price)

def current_profit(self_price, rival_price):
    """Calculate profit using the demand and cost constants."""
    quantity = demand_function(a, d, beta, self_price, rival_price)
    return int((self_price - COST) * quantity)

def plot_data(user_id, round_number):
    filename = f'group{session["group"]}.csv'
    file_path = os.path.join('group_data', filename)
    data = {
        'rounds': [],
        'user_prices': [],
        'rival_prices': [],
        'demands': [],
        'profits': [],
        'last_20_rounds': []
    }

    if os.path.exists(file_path):
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            start = max(0, len(rows) - 20)
            for row in rows:
                if int(row['Round']) <= round_number:
                    data['rounds'].append(int(row['Round']))
                    data['user_prices'].append(float(row[f'Price{user_id}']) if row[f'Price{user_id}'] else 0.0)
                    rival_id = '2' if user_id == '1' else '1'
                    data['rival_prices'].append(float(row[f'Price{rival_id}']) if row[f'Price{rival_id}'] else 0.0)
                    data['demands'].append(float(row[f'Demand{user_id}']) if row[f'Demand{user_id}'] else 0.0)
                    data['profits'].append(float(row[f'Profit{user_id}']) if row[f'Profit{user_id}'] else 0.0)
            data['last_20_rounds'] = rows[start:len(rows)]

    return data




def generate_demand_profit_plot(data):
    buf = io.BytesIO()
    plt.figure()
    plt.plot(data['rounds'], data['demands'], label='Demand', color='blue')
    plt.plot(data['rounds'], data['profits'], label='Profit', color='green')
    plt.title('Demand and Profit Over Rounds')
    plt.xlabel('Round')
    plt.ylabel('Values')
    plt.legend()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plot_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return plot_base64

def generate_price_plot(data):
    buf = io.BytesIO()
    plt.figure()
    plt.plot(data['rounds'], data['user_prices'], label=f'Your Prices', color='red')
    plt.plot(data['rounds'], data['rival_prices'], label=f'Rival Prices', color='orange')
    plt.title('Pricing Comparison')
    plt.xlabel('Round')
    plt.ylabel('Price')
    plt.legend()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plot_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return plot_base64


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user = request.form.get('user')
        price = request.form.get('price')
        if user:
            # Store the user in the session and initialize other values
            session['user'] = int(user)
            session['group'] = 1  # Assigning all users to Group 1 initially
            session['round'] = 1  # Initialize round number
            return redirect(url_for('index'))
        if price:
            # Handle price submission and update CSV
            update_csv(session['group'], session['user'], session['round'], price)
            session['round'] += 1
            if session['round'] > 200:
                return redirect(url_for('completion'))
            flash('Price updated successfully!', 'success')
            return redirect(url_for('results', round_number=session['round'] - 1))
    # Ensure user, group, and round information is available for the template
    return render_template('index.html', group=session.get('group', 1), user=session.get('user'), round=session.get('round', 1))

def update_csv(group, user, round_number, price):
    """Update or create CSV files to store round information."""
    filename = f'group{group}.csv'
    file_path = os.path.join('group_data', filename)
    temp_file_path = os.path.join('group_data', f'temp_{filename}')
    round_exists = False
    previous_assets = [0, 0] 

    if os.path.exists(file_path):
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            # Load last known assets from the last row before the current round
            for row in reader:
                if int(row['Round']) < round_number:
                    previous_assets = [float(row['Asset1'] or 0), float(row['Asset2'] or 0)]

    with open(temp_file_path, 'w', newline='') as temp_file:
        fieldnames = ['Round', 'Price1', 'Demand1', 'Profit1', 'Asset1', 'Price2', 'Demand2', 'Profit2', 'Asset2']
        writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
        if os.path.exists(file_path):
            with open(file_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                writer.writeheader()
                for row in reader:
                    if int(row['Round']) == round_number:
                        if user == 1:
                            row['Price1'] = price
                        elif user == 2:
                            row['Price2'] = price
                        if row['Price1'] and row['Price2']:
                            row['Demand1'] = demand_function(a, d, beta, float(row['Price1']), float(row['Price2']))
                            row['Profit1'] = current_profit(float(row['Price1']), float(row['Price2']))
                            row['Asset1'] = previous_assets[0] + float(row['Profit1'])
                            previous_assets[0] += float(row['Profit1'])
                            row['Demand2'] = demand_function(a, d, beta, float(row['Price2']), float(row['Price1']))
                            row['Profit2'] = current_profit(float(row['Price2']), float(row['Price1']))
                            row['Asset2'] = previous_assets[1] + float(row['Profit2'])
                            previous_assets[1] += float(row['Profit2'])
                        round_exists = True
                    writer.writerow(row)
        if not round_exists:
            if not os.path.exists(file_path):
                writer.writeheader()
            new_row = {'Round': round_number, 'Price1': '', 'Price2': '', 'Demand1': '', 'Demand2': '', 'Profit1': '', 'Profit2': '',  'Asset1': previous_assets[0], 'Asset2': previous_assets[1]}
            if user == 1:
                new_row['Price1'] = price
                new_row['Profit1'] = current_profit(float(price), 0)  # Assuming 0 as rival price initially
                new_row['Asset1'] += new_row['Profit1']
                
            elif user == 2:
                new_row['Price2'] = price
                new_row['Profit2'] = current_profit(float(price), 0)  # Assuming 0 as rival price initially
                new_row['Asset2'] += new_row['Profit2']
                
            writer.writerow(new_row)
    # Replace the old file with the updated one
    os.replace(temp_file_path, file_path)

@app.route('/results/<int:round_number>', methods=['GET'])
def results(round_number):
    if round_number > 200:
        return redirect(url_for('completion'))
    user_id = str(session['user'])
    filename = f'group{session["group"]}.csv'
    file_path = os.path.join('group_data', filename)
    prices = {}
    data = plot_data(user_id, round_number)
    demand_profit_plot = generate_demand_profit_plot(data)
    price_plot = generate_price_plot(data)
    all_submitted = False


    if os.path.exists(file_path):
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if int(row['Round']) == round_number:
                    prices = row
                    if row['Price1'] and row['Price2']:  # Check if both prices are submitted
                        all_submitted = True
                        data = plot_data(user_id, round_number)
                    break

    return render_template('results.html', round=round_number, user=session['user'], prices = prices, all_submitted=all_submitted, demand_profit_plot=demand_profit_plot, price_plot=price_plot, last_20_rounds=data['last_20_rounds'])

@app.route('/completion', methods=['GET'])
def completion():
    return render_template('completion.html')


@socketio.on('connect')
def on_connect():
    print("Client connected")
    # Start the filesystem monitor in a background thread
    #thread = threading.Thread(target=start_file_monitor)
    #thread.daemon = True  # Daemon threads exit when the program does
    #thread.start()
    executor.submit(start_file_monitor)

if __name__ == '__main__':
    try:
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    finally:
        executor.shutdown(wait=True)
