from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
load_dotenv()
import os
import smtplib
import random
from datetime import datetime
import requests
import json
from constants import Sections, PopularBooks, PopularCoverIdxs, ITEMS_IN_PAGE
from meta import popular_page, explore_page
import copy
######################## contants #############################
SECTIONS = Sections()
saved_covers = []

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

# many to many relation between Book and Search
class book_search(db.Model):
    __tablename__ = 'book_search'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    search_id = db.Column(db.Integer, db.ForeignKey('search.id'), nullable=False)

# Search DB
class Search(db.Model):
    __tablename__ = 'search'
    id = db.Column(db.Integer, primary_key=True)
    searchTerm = db.Column(db.String(200), unique=True, nullable=False)

# User Book database to store its unique id, searches, 
class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    coverId = db.Column(db.String(100), unique=True, nullable=False)
    bookName = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    # price = db.Column(db.Float, nullable=False)
    publishedYear = db.Column(db.Integer, nullable=False)
    editionCount = db.Column(db.Integer, nullable=False)
    searches = db.relationship('Search', secondary=book_search.__tablename__, lazy='subquery',
        backref=db.backref('books', lazy=True))

# Notification DB
class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    isRead = db.Column(db.Boolean(), default=False)

# class Section(db.Model):
#     pass

with app.app_context():
    db.create_all()

############################ Routes ################################################

# index route always opens signup page
@app.route('/')
def home():

    update_saved_covers()
    print(session.keys())
    if "temp_user" in set(session.keys()):
        print("temp user exist")
    else:
        print("temp user dosen't exist")

    # print("session['temp_user'] = ", session['temp_user'])
    return render_template('login_page.html')

# login_page route opens login page
@app.route('/login_page')
def login_page():
    
    return render_template('login_page.html')

@app.route('/signup_page')
def signup_page():
    return render_template('signup_page.html')

# verification_page route opens verification page
@app.route('/verifcation_page')
def verification_page():
    session['forgot verify'] = True
    return render_template('verification_page.html', state='forgot verify')

# forgot_password_page open forgot password page
@app.route('/forgot_password_page')
def forgot_password_page():
    return render_template('/forgot_password_page.html', state='valid')

@app.route('/home_page')
def home_page():
    global saved_covers 

    search({"book": {'q': 'Beloved by Toni Morrison'}})
    update_saved_covers()
    cover_ids = []
    book_names = []
    published_years = []
    authors = [] 
    edition_counts = []
    unsaved_covers = []

    if SECTIONS.CURRENT_SECTION == SECTIONS.POPULARP_PRODUCTS:
        
        for i in range(len(PopularBooks)):
            popularBook = PopularBooks[i]

            recived_book_names, recived_cover_ids, recived_published_years, recived_authors, recived_edition_counts = search({"book": {'q': popularBook}})

            if len(recived_book_names) >= PopularCoverIdxs[i]:
                book_names.append(recived_book_names[PopularCoverIdxs[i]])    
                cover_ids.append(recived_cover_ids[PopularCoverIdxs[i]])
                published_years.append(recived_published_years[PopularCoverIdxs[i]])
                authors.append(recived_authors[PopularCoverIdxs[i]])
                edition_counts.append(recived_edition_counts[PopularCoverIdxs[i]])
            else:
                book_names.append(recived_book_names[0])    
                cover_ids.append(recived_cover_ids[0])
                published_years.append(recived_published_years[PopularCoverIdxs[0]])
                authors.append(recived_authors[PopularCoverIdxs[0]])
                edition_counts.append(recived_edition_counts[PopularCoverIdxs[0]])
            
            if cover_ids[-1] not in saved_covers:
                unsaved_covers.append(cover_ids[-1])

        print("unsaved_cover = ", unsaved_covers)
        print("#################################### END OF UNSAVED COVERS ####################################")
        if len(unsaved_covers) != 0:
            for unsaved_cover in unsaved_covers:
                fetchCovers(unsaved_cover)
    elif SECTIONS.CURRENT_SECTION == SECTIONS.EXPLORE:
        book_names, cover_ids, published_years, authors, edition_counts = fetchBooksForExplore()

        for cover_id in cover_ids:
            if cover_id not in saved_covers:
                unsaved_covers.append(cover_id)

        if len(unsaved_covers) != 0:
            for unsaved_cover in unsaved_covers:
                fetchCovers(unsaved_cover)



    # fetchCovers(cover_ids)
    print(book_names)
    print(cover_ids)
    return render_template('home_page.html',
                            book_names=book_names,
                              cover_ids=cover_ids, 
                              published_years=published_years, 
                              authors=authors, 
                              edition_counts=edition_counts,
                              sections=SECTIONS.getSections(),
                              current_section=SECTIONS.CURRENT_SECTION,
                              page=popular_page)

@app.route('/update_home_page')
def update_home_page():
    global saved_covers

    update_saved_covers()
    cover_ids = []
    book_names = []
    unsaved_covers = []

    if SECTIONS.CURRENT_SECTION == SECTIONS.POPULARP_PRODUCTS:
        
        for i in range(len(PopularBooks)):
            popularBook = PopularBooks[i]

            print("current popular book = ", popularBook)
            recived_book_names, recived_cover_ids = search({"book": {'q': popularBook}})
            print("recived_book_names = ", recived_book_names)
            if len(recived_book_names) >= PopularCoverIdxs[i]:
                book_names.append(recived_book_names[PopularCoverIdxs[i]])    
                cover_ids.append(recived_cover_ids[PopularCoverIdxs[i]])
            else:
                book_names.append(recived_book_names[0])    
                cover_ids.append(recived_cover_ids[0])
            
            if cover_ids[-1] not in saved_covers:
                unsaved_covers.append(cover_ids[-1])

        
        print("unsaved_cover = ", unsaved_covers)
        print("#################################### END OF UNSAVED COVERS ####################################")
        if len(unsaved_covers) != 0:
            for unsaved_cover in unsaved_covers:
                fetchCovers(unsaved_cover)
    elif SECTIONS.CURRENT_SECTION == SECTIONS.EXPLORE:
        pass

    # fetchCovers(cover_ids)
    print(book_names)
    print(cover_ids)
    return render_template('home_page.html',
                            book_names=book_names,
                                cover_ids=cover_ids,
                                sections=SECTIONS.getSections(),
                                    current_section=SECTIONS.CURRENT_SECTION)

@app.route('/individualproduct_page/<coverId>', methods=["GET", "POST"])
def individualproduct_page(coverId):

    current_book = db.session.query(Book).filter(Book.coverId == coverId).first()
    return render_template("individualproduct_page.html", coverId=coverId, book=current_book)

@app.route('/notification_page', methods=['GET'])
def notification_page():
    userEmail = session['user']
    userNotifications = db.session.query(Notification).filter(Notification.user == userEmail).all()
    print("len(userNotifications) = ", len(userNotifications))
    current_notifications = copy.deepcopy(userNotifications)

    for notification in userNotifications:
        notification.isRead = True
    
    db.session.commit()

    return render_template("notifications_page.html", notifications=current_notifications)
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
    
    session.clear()
    session['loggedIn'] = True
    session['user'] = email
    print(session)
    # if all of the above failuer cases fail user will be directed to homepage
    return redirect('/home_page')

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
        
        session.clear()
        session['loggedIn'] = True
        session['user'] = email
        return redirect('/home_page')
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

@app.route('/logout', methods=['GET'])
def logout():
    session['loggedIn'] = False
    session.pop('user')

    return redirect('/login_page')

@app.route('/nextPageClicked/<section>', methods=['GET', 'POST'])
def nextPageClicked(section):
    global explore_page, recommendation_page, popular_page
    print("nextPage cliecked")

    if section == SECTIONS.POPULARP_PRODUCTS:
        if popular_page != 1:
            popular_page = 2
    elif section == SECTIONS.EXPLORE:
        explore_page += 1
    return redirect('/home_page')

@app.route('/prevPageClicked/<section>', methods=['GET', 'POST'])
def prevPageClicked(section):
    global explore_page, recommendation_page, popular_page
    print("prevPage cliecked")

    if section == SECTIONS.POPULARP_PRODUCTS:
        if popular_page == 3:
            popular_page = 2
        
        elif popular_page == 2:
            popular_page = 1
    elif section == SECTIONS.EXPLORE:
        if explore_page - 1 != 0:
            explore_page -= 1
    return redirect('/home_page')


@app.route('/sectionClicked/<section>', methods=['GET', 'POST'])
def sectionClicked(section):

    SECTIONS.CURRENT_SECTION = section

    return redirect('/home_page')
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
    
def search(searchBy):
    # if already searched return previous result
    itemType = list(searchBy.keys())[0]
    searchQuery = list(searchBy.values())[0]
    searchTerm = ""
    if itemType == 'book':
        searchTerm = searchQuery['q']
    else:
        searchTerm = str(searchQuery)

    searchItem = Search.query.filter_by(searchTerm=searchTerm).first()
    print("searchItem = ", searchItem)
    if searchItem != None:
        print("ENTERED IF\n\n")
        print("search Id = ", searchItem.id)
        bookResults = [db.session.query(Book).filter(Book.id == book_search_item.book_id).first() for book_search_item in db.session.query(book_search).filter(book_search.search_id == searchItem.id).all()]

        # print("search ids = ", [book_search_item.id for book_search_item in db.session.query(book_search).filter(book_search.search_id == searchItem.id).all()])
        book_names = [bookResult.bookName for bookResult in bookResults]
        cover_ids = [bookResult.coverId for bookResult in bookResults]

        return book_names, cover_ids

    print("NOT ENTERED IF \n\n\n")

    ##### else return new search result and save it in db

    # saving new searchTerm
    searchItem = Search(id=len(Search.query.all())+1, 
                        searchTerm=searchTerm)
    db.session.add(searchItem)
    db.session.commit()

    # getting search results
    response = requests.get('https://openlibrary.org/search.json?', params=searchQuery)

    if response.status_code != 200:
        raise Exception('Failed to search Open Library: {} {}'.format(
            response.status_code, response.content
    ))
    else:
        print("search sucessfull")

    # Parse the JSON response.
    books = json.loads(response.content)['docs']

    print(response.text)
    print("books = ", len(books))
    # Get a list of book names.
    book_names = []
    cover_ids = []

    for book in books:
        
        if 'cover_i' in book:
            book_names.append(book['title'])
            cover_ids.append(book['cover_i'])
            print(book['cover_i'])

            # if book already exist in table just create new association with search
            existingBook = db.session.query(Book).filter(Book.bookName == book['title']).first()

            if existingBook != None:
                new_book_search = book_search(id=len(book_search.query.all())+1,book_id=existingBook.id, 
                            search_id=searchItem.id)
                db.session.add(new_book_search)
            else: # else create new book and then create association with search
                newBook = Book(id=len(Book.query.all())+1,
                               bookName=book['title'],
                               coverId=book['cover_i'])
                db.session.add(newBook)
                
                print("newBook.id = ", newBook.id)
                print("searccItem.id = ", searchItem.id)
                new_book_search = book_search(id=len(book_search.query.all())+1, book_id=newBook.id, 
                            search_id=searchItem.id)
                
                db.session.add(new_book_search)
            
            db.session.commit()

    return book_names, cover_ids

def fetchBooksForExplore():
    global explore_page
    url = 'http://openlibrary.org/search.json'


    params = {
    "q": "*",
    "limit": ITEMS_IN_PAGE,
    "page": explore_page
    }
    
    # response = requests.get(url, params=params)
    # data = response.json()
    
    # if not data['docs']:
    #     print("nomore data")
    
    return search({'all_books': params})  

def fetchCovers(cover_ids):
    cover_ids = [cover_ids]
    for cover_id in cover_ids:
        print("cover_id = ", cover_id)
        # break
        cover_image_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        # image_directory = os.path.join(home_directory, "images")
        # if not os.path.exists(image_directory):
        #     os.mkdir(image_directory)

        # Download the cover image.
        response = requests.get(cover_image_url)

        image_directory = os.path.join('static', "covers")
        if not os.path.exists(image_directory):
            os.mkdir(image_directory)

        # Check the response status code.
        if response.status_code != 200:
            raise Exception('Failed to download cover image: {} {}'.format(
                response.status_code, response.content
            ))

        # Save the cover image to a file.
        with open(os.path.join(image_directory, f"{cover_id}.jpg"), 'wb') as f:
            f.write(response.content)

        update_saved_covers()

def getSavedCovers(directory_path):

  filenames = []

  for filename in os.listdir(directory_path):
    # Filter out directories.
    if not os.path.isdir(os.path.join(directory_path, filename)):
      # Remove the extension.
      filename_without_extension = os.path.splitext(filename)[0]
      # Add the filename to the list.
      filenames.append(filename_without_extension)

  return filenames

def update_saved_covers():
    global saved_covers

    saved_covers = set(getSavedCovers('static/covers'))
# send_notification("pythontest363@gmail.com")

# book_names, cover_ids = search("3 mistakes of my life")

if __name__ == '__main__':
    app.run(debug=True)

