import secrets
from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from flask_cors import CORS
import sqlite3
from otp_2fa import send_otp, send_otp_reset_password_email

# config
from config import db_name, flask_secret_key

app = Flask(__name__)
cors = CORS(app)

app.secret_key = flask_secret_key


# Database
def userexists(name_variables):
    try:
        name_variables = name_variables.lower()
        users = []
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (name_variables,))
        user = c.fetchone()
        users.append(user)

        c.execute("SELECT * FROM users WHERE username = ?", (name_variables,))
        user = c.fetchone()
        users.append(user)
        conn.close()

        if users[0] or users[1]:
            return True
        else:
            return False

    except Exception as e:
        print(e)
        return False


def saveuser(userinfo):
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        # save user
        c.execute('''INSERT INTO users (uid, username, first_name, surname, password, email, phone, verified_email)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
            userinfo['uid'], None, userinfo['name1'], userinfo['name2'], userinfo['password'], userinfo['email'],
            userinfo['phone'],
            False))
        conn.commit()

        # save otp
        c.execute('''INSERT INTO otp_codes (uid, code)
                     VALUES (?, ?)''', (
            userinfo['uid'], userinfo['otp']))
        conn.commit()

        conn.close()

        send_otp(userinfo['otp'], userinfo['email'])

        return True
    except Exception as e:
        print(e)
        return False


@app.route('/', methods=['GET'])
def index():
    if "uid" in session:
        return redirect(url_for("dashboard"))

    return render_template('landing_page.html', active_page="index")


@app.route('/test', methods=['GET'])
def test():
    return render_template('test.html')


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name1 = data.get('registerName1')
    name2 = data.get('registerName2')
    password = data.get('password1')
    otp_method = data.get('registerOtp')
    email = data.get('email')
    phone = data.get('phone')

    # check if user exists
    existuser = userexists(email)

    if existuser:
        # check if user email is verified and delete user if not
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if not user[8]:
            # delete user
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE email = ?", (email,))
            conn.commit()

            # delete otp
            c.execute("DELETE FROM otp_codes WHERE uid = ?", (user[1],))
            conn.commit()
            conn.close()

        else:
            return jsonify({
                'success': False,
                'message': 'User already exists!'
            })

    # Generate OTP
    otp = secrets.token_hex(3)

    # TODO: otf verification

    uid = secrets.token_hex(16)

    # save user
    userinfo = {
        'uid': uid,
        'name1': name1,
        'name2': name2,
        'password': password,
        'otp_method': otp_method,
        'email': email,
        'phone': phone,
        'otp': otp
    }

    state = saveuser(userinfo)

    if state:
        session["uid"] = uid
        return jsonify({
            'success': True,
            'message': 'Account created successfully!'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Account creation failed!'
        })


# otp
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    otp = data.get('code2fa')

    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM otp_codes WHERE uid = ?", (session["uid"],))
        otp_code = c.fetchone()
        conn.close()

        if otp_code[2] == otp:
            # update verified_email
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("UPDATE users SET verified_email = ? WHERE uid = ?", (True, session["uid"]))
            conn.commit()

            # delete otp
            c.execute("DELETE FROM otp_codes WHERE uid = ?", (session["uid"],))
            conn.commit()

            conn.close()

            return jsonify({
                'success': True,
                'message': 'OTP verified successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Incorrect OTP!'
            })

    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'OTP verification failed!'
        })


# Username set successfully
@app.route('/setusername', methods=['POST'])
def setusername():
    data = request.get_json()
    new_username = data.get('newUsername')

    # check if username is already taken
    # TODO:
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (new_username,))
        user = c.fetchone()
        conn.close()

        if user:
            return jsonify({
                'success': False,
                'message': 'Username already taken!'
            })
        else:
            allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
            for char in new_username:
                if char not in allowed_chars:
                    return jsonify({
                        'success': False,
                        'message': f'Username contains invalid characters ( {char} )'
                    })

            # update username
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("UPDATE users SET username = ? WHERE uid = ?", (new_username, session["uid"]))
            conn.commit()
            conn.close()

            session["username"] = new_username
            return jsonify({
                'success': True,
                'message': 'Username set successfully'
            })

    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Username set failed!'
        })


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        if "uid" in session:
            return redirect(url_for("index"))
        return render_template('auth.html')

    if request.method == "POST":
        # Get user details from the request
        data = request.get_json()
        email_phone_username = (data.get('nameEmailPhone')).lower()
        password = data.get('loginPass')

        print(email_phone_username, password)

        # Check if user exists
        existuser = userexists(email_phone_username)

        if existuser:
            users = []
            # Get user details
            if "@" in email_phone_username:
                conn = sqlite3.connect(db_name)
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE email = ?", (email_phone_username,))
                user = c.fetchone()
                users.append(user)
            else:
                conn = sqlite3.connect(db_name)
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username = ?", (email_phone_username,))
                user = c.fetchone()
                users.append(user)
                conn.close()

            # check if email is verified
            if not users[0][8]:
                return jsonify({
                    'success': False,
                    'message': 'Email not verified, please sign up again and complete the verification process!'
                })

            # Check if password matches
            for user in users:
                if user is None:
                    continue
                if user[5] == password:
                    session["uid"] = user[1]
                    session["username"] = user[2]
                    return jsonify({
                        'success': True,
                        'message': 'Logged in successfully!'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Incorrect password!'
                    })
        else:
            return jsonify({
                'success': False,
                'message': 'User does not exist!'
            })


@app.route('/resetpass', methods=['POST'])
def reset_password():
    data = request.get_json()
    email_phone = (data.get('resetEmailNamePhone')).lower()

    # Check if user exists
    existuser = userexists(email_phone)

    if existuser:
        # send reset email/message
        otp = secrets.token_hex(3)

        if "@" in email_phone:
            send_otp_reset_password_email(otp, email_phone)
        else:
            # fetch email
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ?", (email_phone,))
            user = c.fetchone()
            conn.close()

            send_otp_reset_password_email(otp, user[6])

        # remove old otp
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("DELETE FROM reset_codes WHERE email_username = ?", (email_phone,))
        conn.commit()

        # save otp
        c.execute('''INSERT INTO reset_codes (email_username, code)
                     VALUES (?, ?)''', (
            email_phone, otp))
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'message': 'Check your email for an otp code!'
        })

    else:
        return jsonify({
            'success': False,
            'message': 'User does not exist!'
        })


@app.route('/verify_reset', methods=['POST'])
def verify_reset():
    data = request.get_json()
    otp = data.get('resetCode')
    email_name = (data.get('resetEmailNamePhone')).lower()

    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM reset_codes WHERE email_username = ?", (email_name,))
        reset_code = c.fetchone()
        conn.close()

        if reset_code[2] == otp:
            return jsonify({
                'success': True,
                'message': 'OTP verified successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Incorrect OTP!'
            })

    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'OTP verification failed!'
        })


@app.route('/setnewpass', methods=['POST'])
def setnewpass():
    data = request.get_json()
    new_password = data.get('newPassword')
    email_name = (data.get('resetEmailNamePhone')).lower()
    otp = data.get('resetCode')

    # check if otp is correct
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM reset_codes WHERE email_username = ?", (email_name,))
        reset_code = c.fetchone()
        conn.close()

        # standard
        if "@" in email_name:
            email = email_name
        else:
            # fetch email
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ?", (email_name,))
            user = c.fetchone()
            conn.close()

            email = user[6]

        # verify otp
        if reset_code[2] == otp:
            # update password
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
            conn.commit()

            # delete otp
            c.execute("DELETE FROM reset_codes WHERE email_username = ?", (email,))
            conn.commit()
            conn.close()

            # fetch user
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email = ?", (email,))
            user = c.fetchone()
            conn.close()

            session["uid"] = user[1]
            session["username"] = user[2]

            return jsonify({
                'success': True,
                'message': 'Password updated successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Incorrect OTP!'
            })



    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Password update failed!'
        })


@app.route("/logout")
def logout():
    session.clear()
    flash("success_Logged out")
    return redirect(url_for("index"))


# account
@app.route("/account")
def account():
    if "uid" not in session:
        return redirect(url_for("login"))

    # fetch user
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE uid = ?", (session["uid"],))
    user = c.fetchone()
    conn.close()

    print(user)

    user_info = {
        'username': user[2],
        'email': user[6],
        'phone': user[7],
        'account_deleted': user[9],
    }

    print(user_info)

    return render_template("account.html", active_page="account", account=user_info)


# /change_password (currentPassword, newPassword, confirmPassword)
@app.route("/change_password", methods=['POST'])
def change_password():
    data = request.get_json()
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    confirm_password = data.get('confirmPassword')

    # check if new password matches confirm password
    if new_password != confirm_password:
        return jsonify({
            'success': False,
            'message': 'New password does not match confirm password!'
        })

    # check if current password is correct
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE uid = ?", (session["uid"],))
        user = c.fetchone()
        conn.close()

        if user[5] == current_password:
            # update password
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("UPDATE users SET password = ? WHERE uid = ?", (new_password, session["uid"]))
            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Password updated successfully!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Incorrect password!'
            })

    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Password update failed!'
        })


# /change_email (newEmail)
@app.route('/change_email', methods=['POST'])
def change_email():
    data = request.get_json()
    new_email = (data.get('newEmail')).lower()
    uid = session["uid"]

    # check if email exists for a separate user
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (new_email,))
        user = c.fetchone()
        conn.close()

        if user:
            return jsonify({
                'success': False,
                'message': 'Email already exists!'
            })
        else:
            # update email
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("UPDATE users SET email = ? WHERE uid = ?", (new_email, uid))
            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Email updated successfully!'
            })

    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Email update failed!'
        })


# /change_number (changeNumber)
@app.route('/change_number', methods=['POST'])
def change_number():
    data = request.get_json()
    new_number = data.get('changeNumber')
    uid = session["uid"]

    # check if number exists for a separate user
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE phone = ?", (new_number,))
        user = c.fetchone()
        conn.close()

        if user:
            return jsonify({
                'success': False,
                'message': 'Number already exists!'
            })
        else:
            # update number
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("UPDATE users SET phone = ? WHERE uid = ?", (new_number, uid))
            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Number updated successfully!'
            })

    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Number update failed!'
        })


# /change_username (newUsername)
@app.route('/change_username', methods=['POST'])
def change_username():
    data = request.get_json()
    new_username = (data.get('newUsername')).lower()
    uid = session["uid"]

    # check if username exists for a separate user
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (new_username,))
        user = c.fetchone()
        conn.close()

        if user:
            # check if same username
            if user[2] == session["username"]:
                return jsonify({
                    'success': False,
                    'message': 'Choose a username different from your current one!'
                })

            return jsonify({
                'success': False,
                'message': 'Username already exists!'
            })
        else:
            # update username
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("UPDATE users SET username = ? WHERE uid = ?", (new_username, uid))
            conn.commit()
            conn.close()

            session["username"] = new_username

            return jsonify({
                'success': True,
                'message': 'Username updated successfully!'
            })

    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Username update failed!'
        })


# /delete_account (deletePassword)
@app.route('/delete_account', methods=['POST'])
def delete_account():
    data = request.get_json()
    password = data.get('deletePassword')

    # check if password is correct and update pending_deletion
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE uid = ?", (session["uid"],))
        user = c.fetchone()
        conn.close()

        if user[5] == password:
            # check if account is already queued for deletion
            if user[9]:
                return jsonify({
                    'success': False,
                    'message': 'Account already queued for deletion!'
                })

            # update pending_deletion
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("UPDATE users SET pending_deletion = ? WHERE uid = ?", (True, session["uid"]))
            conn.commit()
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Account queued for deletion, log in within 7 days to cancel the deletion!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Incorrect password!'
            })

    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Account deletion failed!'
        })


# /cancel_deletion
@app.route('/cancel_delete_account', methods=['POST'])
def cancel_delete_account():
    uid = session["uid"]

    # check if account is queued for deletion
    try:
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE uid = ?", (uid,))
        user = c.fetchone()
        conn.close()

        if not user[9]:
            return jsonify({
                'success': False,
                'message': 'Account is not queued for deletion!'
            })

        # update pending_deletion
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("UPDATE users SET pending_deletion = ? WHERE uid = ?", (False, uid))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Account deletion cancelled successfully!'
        })

    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': 'Account deletion cancellation failed!'
        })


@app.route('/transactions')
def transactions():
    if "uid" not in session:
        return redirect(url_for("login"))
    return render_template("transactions.html", active_page="transactions")


@app.route('/history')
def history():
    if "uid" not in session:
        return redirect(url_for("login"))

    return render_template("history.html", active_page="history")


##tests
@app.route("/dashboards")
def dashboards():
    return render_template("dashboard_alternate.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")


## Ian backend tests
import time


@app.route("/account_info", methods=['POST'])
def get_balance():
    if "uid" not in session:
        return jsonify({
            'success': False,
            'message': 'Please log in to view your account info'
        })

    return jsonify({
        'success': True,
        'balance': '$11,007',
        'balance_text': '+9.7%' + "from last month",
        'transactions': '+14',
        'transactions_text': "" + "in the last week",
    })


@app.route("/transactions", methods=['POST'])
def get_transactions():
    # time.sleep(100)
    return jsonify({
        'success': True,
        'message': 'Transactions fetched successfully!',
        'transactions': [
            {
                'id': 1,
                'date': '2021-08-10',
                'amount': 100,
                'type': 'credit',
                'transaction_id': 'Salary'
            },
            {
                'id': 2,
                'date': '2021-08-11',
                'amount': 50,
                'type': 'debit',
                'transaction_id': 'Food'
            },
            {
                'id': 3,
                'date': '2021-08-12',
                'amount': 100,
                'type': 'credit',
                'transaction_id': 'Salary'
            },
            {
                'id': 4,
                'date': '2021-08-13',
                'amount': 50,
                'type': 'debit',
                'transaction_id': 'Food'
            },
            {
                'id': 5,
                'date': '2021-08-14',
                'amount': 100,
                'type': 'credit',
                'transaction_id': 'Salary'
            },
            {
                'id': 6,
                'date': '2021-08-15',
                'amount': 50,
                'type': 'debit',
                'transaction_id': 'Food'
            },
            {
                'id': 7,
                'date': '2021-08-16',
                'amount': 100,
                'type': 'credit',
                'transaction_id': 'Salary'
            },
            {
                'id': 8,
                'date': '2021-08-17',
                'amount': 50,
                'type': 'debit',
                'transaction_id': 'Food'
            },
            {
                'id': 9,
                'date': '2021-08-18',
                'amount': 100,
                'type': 'credit',
                'transaction_id': 'Salary'
            },
            {
                'id': 10,
                'date': '2021-08-19',
                'amount': 50,
                'type': 'debit',
                'transaction_id': 'Food'
            }
        ]
    })


if __name__ == '__main__':
    app.run(port=8800, host='0.0.0.0', debug=True)
