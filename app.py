from flask import Flask, request, jsonify, session, send_from_directory
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import mysql.connector
from datetime import datetime

app = Flask(__name__, static_folder='static')
app.secret_key = "secretkey"

bcrypt = Bcrypt(app)

CORS(app, supports_credentials=True)

# MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="$Divya@1010",
    database="expense_tracker"
)

cursor = db.cursor(dictionary=True)

@app.route('/')
def home():
    return send_from_directory('static', 'login.html')

@app.route('/login.html')
def login_page():
    return send_from_directory('static', 'login.html')


@app.route('/register.html')
def register_page():
    return send_from_directory('static', 'register.html')


@app.route('/dashboard.html')
def dashboard_page():
    return send_from_directory('static', 'dashboard.html')


@app.route('/expenses.html')
def expenses_page():
    return send_from_directory('static', 'expenses.html')


@app.route('/register', methods=['POST'])
def register():

    data = request.json

    username = data['username']
    email = data['email']
    password = data['password']

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    query = """
    INSERT INTO users(username, email, password)
    VALUES(%s, %s, %s)
    """

    try:
        cursor.execute(query, (username, email, hashed_password))
        db.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except:
        return jsonify({"message": "Username or Email already exists"}), 400


@app.route('/login', methods=['POST'])
def login():

    data = request.json

    email = data['email']
    password = data['password']

    query = "SELECT * FROM users WHERE email=%s"

    cursor.execute(query, (email,))
    user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user['password'], password):

        session['user_id'] = user['id']
        session['username'] = user['username']

        return jsonify({
            "message": "Login successful",
            "username": user['username']
        }), 200

    return jsonify({"message": "Invalid credentials"}), 401


@app.route('/logout')
def logout():

    session.clear()

    return jsonify({"message": "Logged out"}), 200


def check_login():

    if 'user_id' not in session:
        return False

    return True

@app.route('/expenses', methods=['GET'])
def get_expenses():

    if not check_login():
        return jsonify({"message": "Unauthorized"}), 401

    query = """
    SELECT * FROM expenses
    WHERE user_id=%s
    ORDER BY date DESC
    """

    cursor.execute(query, (session['user_id'],))

    expenses = cursor.fetchall()

    return jsonify(expenses), 200

@app.route('/expenses', methods=['POST'])
def add_expense():

    if not check_login():
        return jsonify({"message": "Unauthorized"}), 401

    data = request.json

    title = data['title']
    amount = data['amount']
    category = data['category']
    date = data['date']
    note = data.get('note', '')

    if float(amount) <= 0:
        return jsonify({"message": "Amount must be positive"}), 400

    try:
        datetime.strptime(date, '%Y-%m-%d')
    except:
        return jsonify({"message": "Invalid date format"}), 400

    query = """
    INSERT INTO expenses(user_id, title, amount, category, date, note)
    VALUES(%s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        session['user_id'],
        title,
        amount,
        category,
        date,
        note
    ))

    db.commit()

    return jsonify({"message": "Expense added"}), 201

@app.route('/expenses/<int:id>', methods=['PUT'])
def update_expense(id):

    if not check_login():
        return jsonify({"message": "Unauthorized"}), 401

    data = request.json

    title = data.get('title', '')
    amount = data.get('amount', 0)
    category = data.get('category', '')
    date = data.get('date', '')
    note = data.get('note', '')

    query = """
    UPDATE expenses
    SET title=%s,
        amount=%s,
        category=%s,
        date=%s,
        note=%s
    WHERE id=%s AND user_id=%s
    """

    cursor.execute(query, (
        title,
        amount,
        category,
        date,
        note,
        id,
        session['user_id']
    ))

    db.commit()

    return jsonify({
        "message": "Expense updated successfully"
    }), 200

@app.route('/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):

    if not check_login():
        return jsonify({"message": "Unauthorized"}), 401

    query = """
    DELETE FROM expenses
    WHERE id=%s AND user_id=%s
    """

    cursor.execute(query, (id, session['user_id']))
    db.commit()

    return jsonify({"message": "Expense deleted"}), 200

@app.route('/expenses/summary')
def summary():

    if not check_login():
        return jsonify({"message": "Unauthorized"}), 401

    query = """
    SELECT
    COUNT(*) as total_expenses,
    SUM(amount) as total_amount,
    MAX(amount) as highest_expense
    FROM expenses
    WHERE user_id=%s
    """

    cursor.execute(query, (session['user_id'],))

    data = cursor.fetchone()

    return jsonify(data), 200

@app.route('/expenses/filter')
def filter_expenses():

    if not check_login():
        return jsonify({"message": "Unauthorized"}), 401

    category = request.args.get('category')
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    query = """
    SELECT * FROM expenses
    WHERE user_id=%s
    """

    values = [session['user_id']]

    if category:
        query += " AND category=%s"
        values.append(category)

    if from_date and to_date:
        query += " AND date BETWEEN %s AND %s"
        values.extend([from_date, to_date])

    cursor.execute(query, tuple(values))

    expenses = cursor.fetchall()

    return jsonify(expenses), 200

if __name__ == '__main__':
    app.run(debug=True)