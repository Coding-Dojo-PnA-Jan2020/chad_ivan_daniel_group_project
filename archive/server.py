from flask import Flask, render_template, request, redirect, session, flash, jsonify
from mysqlconnection import connectToMySQL
import re
import base64
import os
#from datetime import datetime
from flask_bcrypt import Bcrypt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from yubico_client.py3 import b
from werkzeug.utils import secure_filename
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 
DATABASE = 'dojo_messages'
app = Flask(__name__)
app.secret_key = "Blahzay Blahzay"
bcrypt = Bcrypt(app)

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {"jpeg", "png", "jpg"}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=['POST'])
def on_register():
    is_valid = True
    if len(request.form['fname']) < 2:
        is_valid = False
        flash("Please enter a first name of at least 2 characters")
    if len(request.form['lname']) < 2:
        is_valid = False
        flash("Please enter a last name of at least 2 characters")
    if len(request.form['email']) < 1:
        is_valid = False
        flash("Email cannot be blank", 'email')
    elif not EMAIL_REGEX.match(request.form['email']):
        is_valid = False
        flash("Invalid email address!", 'email')
    else:
        db = connectToMySQL(DATABASE)
        data = {
            "em": request.form['email']
        }
        result = db.query_db("SELECT * FROM users WHERE email = %(em)s",data)
        if len(result) > 0:
            flash("This email address is already registered.")
            is_valid = False
    if len(request.form['pass']) < 8:
        is_valid = False
        flash("Please enter a password of at least 8 characters")
    if request.form['pass'] != request.form['cpass']:
        is_valid = False
        flash("Passwords do not match")
    if is_valid:
        # include some logic to validate user input before adding them to the database!
        # create the hash
        pw_hash = bcrypt.generate_password_hash(request.form['pass'])  
        # print(pw_hash)  
        # prints something like b'$2b$12$sqjyok5RQccl9S6eFLhEPuaRaJCcH3Esl2RWLm/cimMIEnhnLb7iC'
        # be sure you set up your database so it can store password hashes this long (63 characters)
        email_provided = request.form['email'] # This is input in the form of a string
        email = email_provided.encode() # Convert to type bytes
        salt = b(os.urandom(30)) # CHANGE THIS - recommend using a key from os.urandom(16), must be of type bytes
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        ukey = base64.urlsafe_b64encode(kdf.derive(email))
        print(ukey)
        mysql = connectToMySQL(DATABASE)
        query = """INSERT INTO users 
        (first_name, last_name, email, password, created_at, updated_at) 
        VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s, NOW(), NOW());"""
        data = {
            "fn": request.form["fname"],
            "ln": request.form["lname"],
            "em": request.form["email"],
            "pw": pw_hash
        }
        session['user_id'] = mysql.query_db(query, data)
        # add user to database
        # display success message
        # flash("User successfully added")
        mysql = connectToMySQL(DATABASE)
        query = "INSERT INTO dojo_messages.keys (user_id, user_key) VALUES (%(u_id)s, %(key)s);"
        data = {
            "u_id": session['user_id'],
            "key": ukey
        }
        mysql.query_db(query, data)
        return redirect('/dashboard')
    return redirect('/')

@app.route("/login", methods=["POST"])
def on_login():
    is_valid = True

    if len(request.form['email']) < 1:
        is_valid = False
        flash("Email cannot be blank")
    elif not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        is_valid = False
        flash("Invalid email address!", 'email')
    
    if is_valid:
        mysql = connectToMySQL(DATABASE)
        query = "SELECT user_id, email, password FROM users WHERE email = %(em)s"
        data = {
            "em": request.form['email']
        }
        user_data = mysql.query_db(query, data)

        if user_data:
            user = user_data[0]

            if bcrypt.check_password_hash(user_data[0]['password'], request.form['pass']):
                session['user_id'] = user['user_id']
            # verify password
            # print(user_data)
                return redirect("/dashboard")
            else:
                flash("Email/Password combo is invalid")
                return redirect("/")
        else:
            flash("Please register first")
            return redirect("/")
    else:
        return redirect("/")

@app.route('/logout')
def on_logout():
    session.clear()
    return redirect("/")

@app.route('/dashboard')
def on_messages_dashboard():
    if 'user_id' not in session:
        return redirect('/')
    mysql = connectToMySQL(DATABASE)
    query = "SELECT first_name, last_name, avatar, bio FROM users WHERE user_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    user_data = mysql.query_db(query, data)
    if user_data:
        user_data = user_data[0]
    
    mysql = connectToMySQL(DATABASE)
    query = """SELECT *, 
    COUNT(message_like_id) AS likes 
    FROM messages 
    JOIN users ON messages.author_id = users.user_id 
    LEFT JOIN user_likes 
    ON messages.message_id = user_likes.message_like_id 
    GROUP BY messages.message_id ORDER BY messages.message_id DESC"""
    whispers = mysql.query_db(query, data)

    mysql = connectToMySQL(DATABASE)
    query = "SELECT followed_id FROM followers WHERE follower_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    followed_users = mysql.query_db(query, data)
    followed_ids = [data['followed_id'] for data in followed_users]
    print(followed_ids)

    mysql = connectToMySQL(DATABASE)
    query = "SELECT follower_id FROM followers WHERE followed_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    follower_users = mysql.query_db(query, data)
    follower_ids = [data['follower_id'] for data in follower_users]
    print(follower_ids)

    mysql = connectToMySQL(DATABASE)
    query = "SELECT users.user_id, users.first_name, users.last_name FROM users WHERE users.user_id != %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    users = mysql.query_db(query, data)

    mysql = connectToMySQL(DATABASE)
    query = "SELECT user_key FROM dojo_messages.keys WHERE user_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    key_data = mysql.query_db(query, data)
    if key_data:
        key_data = key_data[0]

    # mysql = connectToMySQL(DATABASE)
    # query = """SELECT messages.author_id, messages.message_id, messages.message, dojo_messages.keys.user_key, users.first_name, users.last_name, users.user_id 
    #             FROM messages 
    #             JOIN dojo_messages.keys 
    #             ON messages.author_id = dojo_messages.keys.user_id
    #             JOIN users ON messages.author_id = users.user_id 
    #             LEFT JOIN user_likes 
    #             ON messages.message_id = user_likes.message_like_id"""
    #             # ORDER BY messages.message_id DESC"""
    # dec_whispers = mysql.query_db(query, data)

    following_followed = [session['user_id']]
    if follower_ids:
        for j in follower_ids:
            if j in followed_ids:
                is_okay = True
                following_followed.append(j)
                print(True)
            else:
                is_okay = False
                dec_whispers = []
                print(False)
    else:
        is_okay = False
        dec_whispers = []
        print(False)
    print(f"Annie are you okay? {is_okay}")
    # if is_okay:
    # for i in following_followed:
    print(f"following_followed iteration: {following_followed}")
    mysql = connectToMySQL(DATABASE)
    query = """SELECT messages.author_id, messages.message_id, messages.message, dojo_messages.keys.user_key, users.first_name, users.last_name, users.user_id 
                FROM messages 
                JOIN dojo_messages.keys 
                ON messages.author_id = dojo_messages.keys.user_id
                JOIN users ON messages.author_id = users.user_id 
                LEFT JOIN user_likes 
                ON messages.message_id = user_likes.message_like_id"""
                # WHERE users.user_id = %(u_id)s OR users.user_id =  %(s_id)s"""
                # ORDER BY messages.message_id DESC"""
    # data = {
    #     'u_id': following_followed,
    #     's_id': session['user_id']
    # }
    dec_whispers = mysql.query_db(query, data)
    # print(dec_whispers)
    for k in dec_whispers:
        # print(following_followed)
        # print(k['author_id'])
        # print(type(k['author_id']))
        if k['author_id'] in following_followed:
            print(k)
            # print(dec_whispers)
            # print(k['user_key'])
            key = (k['user_key'])
            f = Fernet(key)
            k['message'] = f.decrypt(b(k['message']), ttl=None)
            k['message'] = k['message'].decode("utf-8")

    mysql = connectToMySQL(DATABASE)
    query = "SELECT user_key FROM dojo_messages.keys WHERE user_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    key_data = mysql.query_db(query, data)
    if key_data:
        key_data = key_data[0]

    return render_template("dashboard.html", user_data=user_data, whispers=whispers, key_data=key_data, dec_whispers=dec_whispers, followed_ids=followed_ids)

def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_img', methods=['GET', 'POST'])
def upload_img():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Please select a file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
            mysql = connectToMySQL(DATABASE)
            query = "UPDATE users SET avatar = %(av)s WHERE user_id = %(u_id)s"

            data = {
                "av": filename,
                "u_id": session['user_id']
            }
            mysql.query_db(query, data)
            return redirect(request.url)
        
    return redirect('/dashboard')

@app.route('/update_bio')
def update_bio():
    mysql = connectToMySQL(DATABASE)
    query = "SELECT bio FROM users WHERE user_id = %(u_id)s"

    data = {
        "u_id": session['user_id']
    }
    bio = mysql.query_db(query, data)
    return render_template("update_bio.html", bio = bio)

@app.route('/edit_bio', methods=['POST'])
def edit_bio():
    mysql = connectToMySQL(DATABASE)
    query = "UPDATE users SET bio = %(bio)s WHERE user_id = %(u_id)s"

    data = {
        "bio": request.form['bio'],
        "u_id": session['user_id']
    }
    mysql.query_db(query, data)

    return redirect('/dashboard')

@app.route("/dashboard/update_bio", methods=["POST"])
def update_bio_api():
    mysql = connectToMySQL(DATABASE)
    query = "UPDATE users SET bio = %(bio)s WHERE user_id = %(u_id)s"

    data = {
        "bio": request.form['bio'],
        "u_id": session['user_id']
    }
    mysql.query_db(query, data)

    return jsonify({"success": "Bio has been successfully updated!"})



@app.route('/write_whisper', methods=['POST'])
def on_add_whisper():
    if 'user_id' not in session:
        return redirect("/")
    is_valid = True
    if len(request.form['a_whisper']) < 5:
        is_valid = False
        flash("Whisper must be at least 5 characters.")
    if is_valid:
        mysql = connectToMySQL(DATABASE)
        query = "SELECT user_key FROM dojo_messages.keys WHERE user_id = %(u_id)s"
        data = {
            'u_id': session['user_id']
        }
        key_data = mysql.query_db(query, data)
        if key_data:
            key_data = key_data[0]
            key = b(key_data['user_key'])
            crypt_message = request.form['a_whisper'].encode()
            f = Fernet(key)
            encrypted_message = f.encrypt(crypt_message)
            # print(f"this is an {encrypted_message} message!!!!!")

        mysql = connectToMySQL(DATABASE)
        query = "INSERT INTO messages (message, author_id, created_at, updated_at) VALUES (%(msg)s, %(a_id)s, NOW(), NOW())"
        data = {
            'msg': encrypted_message,
            'a_id': session['user_id']
        }
        mysql.query_db(query, data)
    return redirect('/dashboard')

@app.route("/delete_whisper/<message_id>")
def on_delete(message_id):

    mysql = connectToMySQL(DATABASE)
    query = "DELETE FROM messages WHERE message_id = %(m_id)s AND author_id = %(u_id)s"
    data = {
        'm_id': message_id,
        'u_id': session['user_id']
    }
    mysql.query_db(query, data)

    return redirect("/dashboard")

@app.route("/ninjas")
def users_to_follow():
    mysql = connectToMySQL(DATABASE)
    query = "SELECT followed_id FROM followers WHERE follower_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    followed_users = mysql.query_db(query, data)
    followed_ids = [data['followed_id'] for data in followed_users]

    mysql = connectToMySQL(DATABASE)
    query = "SELECT users.user_id, users.first_name, users.last_name, users.avatar FROM users WHERE users.user_id != %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    users = mysql.query_db(query, data)
    # print(users)
    return render_template("/follow.html", users=users, followed_ids=followed_ids)

@app.route("/follow/<user_id>")
def follow_this_user_dashboard(user_id):
    mysql = connectToMySQL(DATABASE)
    query = "INSERT INTO followers (follower_id, followed_id) VALUES (%(folwr)s, %(folwd)s)"
    data = {
        'folwr': session['user_id'],
        'folwd': user_id
    }
    mysql.query_db(query, data)
    return redirect("/dashboard")

@app.route("/unfollow/<f_id>")
def on_unfollow_dashboard(f_id):
    mysql = connectToMySQL(DATABASE)
    query = "DELETE FROM followers WHERE follower_id = %(u_id)s AND followed_id = %(f_id)s"
    data = {
        'u_id': session['user_id'],
        'f_id': f_id
    }
    mysql.query_db(query, data)
    return redirect("/dashboard")

@app.route("/follow_user/<user_id>")
def follow_this_user(user_id):
    mysql = connectToMySQL(DATABASE)
    query = "INSERT INTO followers (follower_id, followed_id) VALUES (%(folwr)s, %(folwd)s)"
    data = {
        'folwr': session['user_id'],
        'folwd': user_id
    }
    mysql.query_db(query, data)
    return redirect("/ninjas")

@app.route("/unfollow_user/<f_id>")
def on_unfollow(f_id):
    mysql = connectToMySQL(DATABASE)
    query = "DELETE FROM followers WHERE follower_id = %(u_id)s AND followed_id = %(f_id)s"
    data = {
        'u_id': session['user_id'],
        'f_id': f_id
    }
    mysql.query_db(query, data)
    return redirect("/ninjas")

@app.route("/user_profile/<user_id>")
def user_profile(user_id):
    mysql = connectToMySQL(DATABASE)
    query = "SELECT * FROM users WHERE user_id = %(u_id)s;"
    data = {
        'u_id': user_id
    }
    user_data = mysql.query_db(query, data)

    mysql = connectToMySQL(DATABASE)
    query = """SELECT *, 
    COUNT(message_like_id) AS likes 
    FROM messages 
    JOIN users ON messages.author_id = users.user_id 
    LEFT JOIN user_likes 
    ON messages.message_id = user_likes.message_like_id 
    GROUP BY messages.message_id ORDER BY messages.message_id DESC"""
    whispers = mysql.query_db(query, data)

    mysql = connectToMySQL(DATABASE)
    query = "SELECT followed_id FROM followers WHERE follower_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    followed_users = mysql.query_db(query, data)
    followed_ids = [data['followed_id'] for data in followed_users]
    print(followed_ids)

    mysql = connectToMySQL(DATABASE)
    query = "SELECT follower_id FROM followers WHERE followed_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    follower_users = mysql.query_db(query, data)
    follower_ids = [data['follower_id'] for data in follower_users]
    print(follower_ids)

    mysql = connectToMySQL(DATABASE)
    query = "SELECT users.user_id, users.first_name, users.last_name, users.avatar FROM users WHERE users.user_id != %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    users = mysql.query_db(query, data)

    mysql = connectToMySQL(DATABASE)
    query = "SELECT user_key FROM f8x0a94mtjmenwxa.keys WHERE user_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    key_data = mysql.query_db(query, data)
    if key_data:
        key_data = key_data[0]

    # mysql = connectToMySQL(DATABASE)
    # query = """SELECT messages.author_id, messages.message_id, messages.message, f8x0a94mtjmenwxa.keys.user_key, users.first_name, users.last_name, users.user_id 
    #             FROM messages 
    #             JOIN f8x0a94mtjmenwxa.keys 
    #             ON messages.author_id = f8x0a94mtjmenwxa.keys.user_id
    #             JOIN users ON messages.author_id = users.user_id 
    #             LEFT JOIN user_likes 
    #             ON messages.message_id = user_likes.message_like_id"""
    #             # ORDER BY messages.message_id DESC"""
    # dec_whispers = mysql.query_db(query, data)

    following_followed = [session['user_id']]
    if follower_ids:
        for j in follower_ids:
            if j in followed_ids:
                is_okay = True
                following_followed.append(j)
                print(True)
            else:
                is_okay = False
                dec_whispers = []
                print(False)
    else:
        is_okay = False
        dec_whispers = []
        print(False)
    print(f"Annie are you okay? {is_okay}")
    # if is_okay:
    # for i in following_followed:
    print(f"following_followed iteration: {following_followed}")
    mysql = connectToMySQL(DATABASE)
    query = """SELECT messages.author_id, messages.message_id, messages.message, f8x0a94mtjmenwxa.keys.user_key, users.first_name, users.last_name, users.user_id 
                FROM messages 
                JOIN f8x0a94mtjmenwxa.keys 
                ON messages.author_id = f8x0a94mtjmenwxa.keys.user_id
                JOIN users ON messages.author_id = users.user_id 
                LEFT JOIN user_likes 
                ON messages.message_id = user_likes.message_like_id"""
                # WHERE users.user_id = %(u_id)s OR users.user_id =  %(s_id)s"""
                # ORDER BY messages.message_id DESC"""
    # data = {
    #     'u_id': following_followed,
    #     's_id': session['user_id']
    # }
    dec_whispers = mysql.query_db(query, data)
    # print(dec_whispers)
    for k in dec_whispers:
        # print(following_followed)
        # print(k['author_id'])
        # print(type(k['author_id']))
        if k['author_id'] in following_followed:
            print(k)
            # print(dec_whispers)
            # print(k['user_key'])
            key = (k['user_key'])
            f = Fernet(key)
            k['message'] = f.decrypt(b(k['message']), ttl=None)
            k['message'] = k['message'].decode("utf-8")

    mysql = connectToMySQL(DATABASE)
    query = "SELECT user_key FROM f8x0a94mtjmenwxa.keys WHERE user_id = %(u_id)s"
    data = {
        'u_id': session['user_id']
    }
    key_data = mysql.query_db(query, data)
    if key_data:
        key_data = key_data[0]
    
    return render_template("profile.html", user_data = user_data[0], whispers=whispers, key_data=key_data, dec_whispers=dec_whispers, users = users, followed_ids=followed_ids, follower_ids = follower_ids)

@app.route('/write_whisper_profile', methods=['POST'])
def on_add_whisper_profile():
    if 'user_id' not in session:
        return redirect("/")
    is_valid = True
    if len(request.form['a_whisper']) < 5:
        is_valid = False
        flash("Whisper must be at least 5 characters.")
    if is_valid:
        mysql = connectToMySQL(DATABASE)
        query = "SELECT user_key FROM dojo_messages.keys WHERE user_id = %(u_id)s"
        data = {
            'u_id': session['user_id']
        }
        key_data = mysql.query_db(query, data)
        if key_data:
            key_data = key_data[0]
            key = b(key_data['user_key'])
            crypt_message = request.form['a_whisper'].encode()
            f = Fernet(key)
            encrypted_message = f.encrypt(crypt_message)
            # print(f"this is an {encrypted_message} message!!!!!")

        mysql = connectToMySQL(DATABASE)
        query = "INSERT INTO messages (message, author_id, created_at, updated_at) VALUES (%(msg)s, %(a_id)s, NOW(), NOW())"
        data = {
            'msg': encrypted_message,
            'a_id': session['user_id']
        }
        mysql.query_db(query, data)
    return redirect(request.referrer)

@app.route("/contact_us")
def contact_us():
    return render_template("/contact.html")

if __name__ == "__main__":
    app.run(debug=True)
