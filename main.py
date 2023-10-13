from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
load_dotenv()
import os
import smtplib
import random
from datetime import datetime
######################## configuring flask app #############################
app = Flask(__name__)

app.secret_key = 'your_secret_key'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

db = SQLAlchemy(app)


############################# Database ######################################
class User(db.Model):
    id = db.Column(db.Integer, unique=True, nullable=False)
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    isVerified = db.Column(db.Boolean(), default=False)
    otp = db.Column(db.String(10), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

############################ Routes ################################################
@app.route('/')
def index():
    if "temp_user" in set(session.keys()):
        print("temp user exist")
    else:
        print("temp user dosen't exist")

    # print("session['temp_user'] = ", session['temp_user'])
    return render_template('signup_page.html')

@app.route('/login_page')
def login_page():
    
    return render_template('login_page.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    print(len(User.query.all()))
    print(request.form)
    

    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    password = request.form['password']
    confirmPassword = request.form['confirmPassword']

    userWithEmail = db.session.get(User, email)

    if password != confirmPassword:
        print("password dosen't match")
    elif userWithEmail != None:
        print("User with this email already exist")
    else:
        otp = send_notification(email)
        newUser = User(id=len(User.query.all())+1,
                   firstName=firstName,
                   lastName=lastName,
                   email=email,
                   password=password,
                   otp=otp)
        
        db.session.add(newUser)
        db.session.commit()

        
        session['temp_user'] = email
        return render_template('verification_page.html', state="unverifed")

    print("registered user")

    return "<h1>error message will be displayed, for improper signup deails format</h1>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    userWithEmail = db.session.get(User, email)

    if userWithEmail == None:
        return "<h1> user with give email doesn't exist </h1>"
    elif password != userWithEmail.password:
        return "<h1> Incorrect password </h1>"
    elif not userWithEmail.isVerified:
        otp = send_notification(email)
        userWithEmail.otp = otp
        db.session.commit()
        return render_template('verification_page.html', state="unverified")

    print("login successful and will be redirected to home page")


    return "<h1> login successful and will be redirected to home page </h1>"

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    otp = request.form['verification_code']
    email = session['temp_user']
    userWithEmail = db.session.get(User, email)

    if otp == userWithEmail.otp:
        userWithEmail.isVerified = True
        db.session.commit()
        return "<h1>otp matched, will be redirected to homepage</h1>"
    else:
        userWithEmail.otp = send_notification(email)
        db.session.commit()
        return render_template("verification_page.html", state="invalid")



################################## helper functions #################################

def send_notification(userEmail):
    verification_code = str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9)) 

    message = "Subject: BookQuest Verifcation Code\n\nyour verification code is " + verification_code + "." 

    with smtplib.SMTP('smtp.office365.com', 587) as connection:
        connection.starttls()
        connection.login(user=os.getenv('EMAIL'), password=os.getenv('PASSWORD'))
        connection.sendmail(from_addr=os.getenv('EMAIL'), to_addrs=userEmail,
                            msg=message)


    
    return verification_code
    
# send_notification("pythontest363@gmail.com")

if __name__ == '__main__':
    app.run(debug=True)

