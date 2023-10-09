from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy

######################## configuring flask app #############################
app = Flask(__name__)

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

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('signup_page.html')

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
        newUser = User(id=len(User.query.all())+1,
                   firstName=firstName,
                   lastName=lastName,
                   email=email,
                   password=password)
        
        db.session.add(newUser)
        db.session.commit()

        return "<h1>Will be redirected to verify.html</h1>"

    print("registered user")

    return "<h1>error message will be displayed, for improper signup deails format</h1>"


if __name__ == '__main__':
    app.run(debug=True)
