from flask import Flask, render_template, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"

db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('signup_page.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    print("registered user")

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
