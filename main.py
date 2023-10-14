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

# index route always opens signup page
@app.route('/')
def index():
    if "temp_user" in set(session.keys()):
        print("temp user exist")
    else:
        print("temp user dosen't exist")

    # print("session['temp_user'] = ", session['temp_user'])
    return render_template('signup_page.html')

# login_page route opens login page
@app.route('/login_page')
def login_page():
    
    return render_template('login_page.html')

# verification_page route opens verification page
@app.route('/verifcation_page')
def verification_page():
    session['forgot verify'] = True
    return render_template('verification_page.html', state='forgot verify')

# forgot_password_page open forgot password page
@app.route('/forgot_password_page')
def forgot_password_page():
    return render_template('/forgot_password_page.html', state='valid')

############################# functionality ##########################################
# register route takes care of user data after register button is clicked
@app.route('/register', methods=['GET', 'POST'])
def register():
    # capturing data filled by user in signup form

    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    password = request.form['password']
    confirmPassword = request.form['confirmPassword']

    userWithEmail = db.session.get(User, email)

    
    if password != confirmPassword: # checking if password and confirm password matches
        print("password dosen't match")
    elif userWithEmail != None: # checkign if users mail is unique or not
        print("User with this email already exist")
    else: # adding user to data base 
        # otp = send_notification(email)
        otp = "0000"
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

    # if all the cases fails appropriate error message will be displayed
    return "<h1>error message will be displayed, for improper signup deails format</h1>"

# login route takes care of user data after login button is clicked
@app.route('/login', methods=['GET', 'POST'])
def login():
    # capturing data filled by the user
    email = request.form['email']
    password = request.form['password']

    # get user with the email form the database
    userWithEmail = db.session.get(User, email)

    if userWithEmail == None: # checking if the user with the email is present in the database
        return "<h1> user with give email doesn't exist </h1>"
    elif password != userWithEmail.password: # checking users password matches with password presend in our database
        return "<h1> Incorrect password </h1>" 
    elif not userWithEmail.isVerified: # checking if authenticated user is a verified user
        otp = send_notification(email)
        userWithEmail.otp = otp
        db.session.commit()
        return render_template('verification_page.html', state="unverified")

    print("login successful and will be redirected to home page")

    # if all of the above failuer cases fail user will be directed to homepage
    return "<h1> login successful and will be redirected to home page </h1>"

# verify route takes care of user verification during signup and reset password processes
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    # verify route keeps track of user to be verified using temp_user value in current flask session

    if "email" in set(request.form.keys()): # checking if the current data recived is from verification page after forgot password is clicked
        # checking if the user exist in database
        userWithEmail = db.session.get(User, request.form['email'])

        # if user doesn't exist in the database error message will be dispalyed
        if userWithEmail == None:
            return render_template('verification_page.html', state='forgot verify email invalid')
        
        # if user is found in database this use will be updated as temp_user 
        session['temp_user'] = request.form['email']

        # redirecting again to the verification page with otp input activated
        return render_template('verification_page.html', state='verify')
    else: # enter else if data is recived from verification page after signup button is clicked
        email = session['temp_user']

    
    userWithEmail = db.session.get(User, email)
    
    # caputring verification code
    otp = request.form['verification_code']

    if otp == userWithEmail.otp: # checking if otp entered matches to the otp sent
        # updating user as verified in the database 
        userWithEmail.isVerified = True
        db.session.commit()

        # checking if forgot verify is in session keys 
        # if true it indicates that user is verified and needs to be redirected to reset password page
        if "forgot verify" in set(session.keys()): 
            session['forgot email'] = email
            return render_template("forgot_password_page.html")
         
        return "<h1>otp matched, will be redirected to homepage</h1>"
    else: # if otp mis-matched they error message will be dispalyed 
        return render_template("verification_page.html", state="invalid")

# update password route is used to reset users password
@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    # caputring new password and its conformation entered by user
    password = request.form['password']
    confirmPassword = request.form['confirmPassword']

    if password == confirmPassword: # if new password matches with conformation password it will be upadated in the database
        userWithEmail = db.session.get(User, session['forgot email'])

        userWithEmail.password = password
        db.session.commit()

        return redirect('/login_page')
    else: # if passwords mis-match error message will be displayed
        return render_template('forgot_password_page.html', state='invalid')


################################## helper functions #################################
# used to send verification mail to user
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

