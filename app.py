from flask import Flask, render_template, redirect, url_for ,request,jsonify
import sqlite3

app = Flask(__name__)

def create_connection():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    return conn, cursor

# Create a table to store user data if it doesn't exist
def create_table():
    conn, cursor = create_connection()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            gender TEXT NOT NULL,
            department TEXT NOT NULL,
            ptype TEXT  -- New column for personality type
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

@app.route('/get_users_data')
def get_users_data():
    conn = sqlite3.connect('user_data.db')  # Replace with your database name
    cursor = conn.cursor()

    # Execute a query to fetch all users
    cursor.execute("SELECT name, email FROM users")  # Replace 'users' with your table name
    existing_users = cursor.fetchall()

    conn.close()

    users_data = [{'name': user[0], 'email': user[1]} for user in existing_users]
    return jsonify(users_data)

@app.route('/check_credentials', methods=['POST'])
def check_credentials():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    conn = sqlite3.connect('user_data.db')  # Replace with your database name
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE name = ? AND email = ?", (name, email))
    
    user = cursor.fetchone()

    conn.close()

    if user:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/redirect_user', methods=['POST'])
def redirect_user():
    if 'testTaker' in request.form:
        return redirect(url_for('index'))
    elif 'admin' in request.form:
        return redirect(url_for('admin'))
    elif 'loginToTest' in request.form:
        return redirect(url_for('loginToTest'))
    elif 'login' in request.form:
        return redirect(url_for('login'))
    else:
        # Handle other cases or errors
        return redirect(url_for('welcome'))

@app.route('/index')
def index():
    return render_template('registration_form.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/loginToTest')
def loginToTest():
    return render_template('loginToTest.html')

@app.route('/login')
def login():
    return render_template('quiz.html')

@app.route('/register', methods=['POST'])
def register():
    create_table()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        gender = request.form['gender']
        department = request.form['department']
        
        conn, cursor = create_connection()
        cursor.execute('''
                INSERT INTO users (name, email, gender, department)
                VALUES (?, ?, ?, ?)
            ''', (name, email, gender, department))
        conn.commit()
        conn.close()
    # Process registration form data if needed
    return redirect(url_for('success'))


@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        # Process quiz answers if needed
        return redirect(url_for('success'))  # Redirect to success page after quiz submission

    return render_template('loginToTest.html')

@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'POST':
        selected_choices = {}
        for i in range(1, 71):
            answer = request.form.get(f'q{i}')
            selected_choices[f'Question {i}'] = answer

        counts = {}
        for col in range(1, 8):
            column_key = f'Column {col}'
            counts[column_key] = {
                'A': sum(1 for idx in range(col, 71, 7) if selected_choices[f'Question {idx}'] == 'a'),
                'B': sum(1 for idx in range(col, 71, 7) if selected_choices[f'Question {idx}'] == 'b')
            }
            ptype = ''
            ptype2 = ''
            combined_ptype = ''

        if counts['Column 1']['A'] > counts['Column 1']['B']:
            ptype += 'E'
            ptype2 += 'E'

        elif counts['Column 1']['A'] < counts['Column 1']['B']:
            ptype += 'I'
            ptype2 += 'I'
        else:
            ptype += 'E'
            ptype2 += 'I'

        # Check for equal counts of N and S
        if counts['Column 2']['A'] + counts['Column 3']['A'] > counts['Column 2']['B'] + counts['Column 3']['B']:
            ptype += 'S'
            ptype2 += 'S'
        elif counts['Column 2']['A'] + counts['Column 3']['A'] < counts['Column 2']['B'] + counts['Column 3']['B']:
            ptype += 'N'
            ptype2 += 'N'
        else:                 # Both N and S are equal
            ptype += 'S'
            ptype2 += 'N'
        if counts['Column 4']['A'] + counts['Column 5']['A'] > counts['Column 4']['B'] + counts['Column 5']['B']:
            ptype += 'T'
            ptype2 += 'T'
        elif counts['Column 4']['A'] + counts['Column 5']['A'] < counts['Column 4']['B'] + counts['Column 5']['B']:
            ptype += 'F'
            ptype2 += 'F'
        else:              # Both T and F are equal
            ptype += 'T'  
            ptype2 += 'F'
        # Check for equal counts of J and P
        if counts['Column 6']['A'] + counts['Column 7']['A'] > counts['Column 6']['B'] + counts['Column 7']['B']:
            ptype += 'J'
            ptype2 += 'J'
        elif counts['Column 6']['A'] + counts['Column 7']['A'] < counts['Column 6']['B'] + counts['Column 7']['B']:
            ptype += 'P'
            ptype2 += 'P'
        else:              # Both J and P are equal
            ptype += 'J'
            ptype2 += 'P'

        user_id = request.form.get('id')  # Assuming user_id is captured in the form
        

        

        if ptype == ptype2:
            print(ptype)
        else:
            combined_ptype = f'{ptype}/{ptype2}'
            print(combined_ptype)

    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

            # Retrieve  record without ptype
        cursor.execute('''
                SELECT id FROM users WHERE ptype IS NULL ORDER BY id DESC LIMIT 1
            ''')
        row = cursor.fetchone()

        if row:
                user_id = row[0]  # Assuming the user's ID is in the first column
                # Update the database with the determined personality type (ptype)
                if combined_ptype:
                    # If combined_ptype exists, update with combined_ptype
                    cursor.execute('''
                        UPDATE users
                        SET ptype = ?
                        WHERE id = ?
                    ''', (combined_ptype, user_id))
                else:
                    # If combined_ptype doesn't exist, update with ptype
                    cursor.execute('''
                        UPDATE users
                        SET ptype = ?
                        WHERE id = ?
                    ''', (ptype, user_id))

                conn.commit()  # Commit changes to the database
        return render_template('result.html', counts=counts, ptype=ptype, combined_ptype=combined_ptype)
    except sqlite3.Error as e:
            print("Database error:", e)  # Print any database-related errors
            conn.rollback()  # Rollback changes if an error occurs
            return "Database error occurred"

    finally:
            conn.close()
    return render_template('result.html', counts=None)

@app.route('/admin_login_submit', methods=['POST'])
def admin_login_submit():
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        # Check admin credentials against the admin table
        cursor.execute('''
            SELECT * FROM admins WHERE username = ? AND password = ?
        ''', (username, password))
        admin = cursor.fetchone()

        if admin:
            # Admin authenticated, fetch user list
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()

            return render_template('user_list.html', users=users)
        else:
            
           return redirect(url_for('admin'))
    except sqlite3.Error as e:
        print("Database error:", e)

    finally:
        conn.close()

    return "Error occurred"  # Adjust this for a proper error message
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()

        return redirect(url_for('admin'))  # Redirect back to the admin panel after deletion
    except sqlite3.Error as e:
        print("Database error:", e)
        conn.rollback()  # Rollback changes if an error occurs

    finally:
        conn.close()

    return "Error occurred"
@app.route('/welcome')
def home():
    # Your logic to render the home page template goes here
    return render_template('welcome.html')

if __name__ == '__main__':
    app.run(debug=True)
