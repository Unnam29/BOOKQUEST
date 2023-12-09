###################### imports ######################  
from flask import Flask, render_template, redirect, request, session, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from dotenv import load_dotenv
load_dotenv()
import os
import smtplib
import random
from datetime import datetime
import requests
import json
from constants import Sections, PopularBooks, PopularCoverIdxs, ITEMS_IN_PAGE, ITEMS_IN_SEARCH_PAGE
from meta import popular_page, explore_page, recommendation_page, search_page_number
import copy
######################## contants #############################
SECTIONS = Sections()
saved_covers = [] # coverids of cached books are stored

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
    _tablename_ = 'book_search'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    search_id = db.Column(db.Integer, db.ForeignKey('search.id'), nullable=False)

# Search DB 
class Search(db.Model):
    _tablename_ = 'search'
    id = db.Column(db.Integer, primary_key=True)
    searchTerm = db.Column(db.String(200), unique=True, nullable=False)

# User Book database to store its unique id, searches, 
class Book(db.Model):
    _tablename_ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    coverId = db.Column(db.String(100), unique=True, nullable=False)
    bookName = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    # price = db.Column(db.Float, nullable=False)
    publishedYear = db.Column(db.Integer, nullable=False)
    editionCount = db.Column(db.Integer, nullable=False)
    searches = db.relationship('Search', secondary=book_search._tablename_, lazy='subquery',
        backref=db.backref('books', lazy=True))

# Notification DB to store notification and associated user ids
class Notification(db.Model):
    _tablename_ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    isRead = db.Column(db.Boolean(), default=False)

# cart-items db to store book ids and associated user ids
class CartItem(db.Model):
    __tablename__ = 'cartitems'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

# orders db to store user order using book_ids and user_ids
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(200), nullable=False)

# whish list db to stores users whishlist items using book_ids and user_ids
class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    cover_id = db.Column(db.Integer, nullable=False)

# review db to stores user reviews to books using user id and book id
class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(500), nullable=False)

with app.app_context():
    db.create_all()

############################ Routes ################################################

# index route always opens signup page
@app.route('/')
def home():

    update_saved_covers()

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
    # route is acessed on when user clicks forgot password to verify user identity
    session['forgot verify'] = True # forgot verify session variable is set to true
    return render_template('verification_page.html', state='forgot verify')

# forgot_password_page open forgot password page
@app.route('/forgot_password_page')
def forgot_password_page():
    return render_template('/forgot_password_page.html', state='valid')

@app.route('/home_page')
def home_page():
    global saved_covers 

    update_saved_covers() # every time home page is visited saved covers are loded into session
    cover_ids = []
    book_names = []
    published_years = []
    authors = [] 
    edition_counts = []
    unsaved_covers = []

    if SECTIONS.CURRENT_SECTION == SECTIONS.POPULARP_PRODUCTS:
        # by deault current section is set to popular products
        
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
            
            # checks if popular books covers exist in saved covers if not add cover id to unsaved_covers
            if cover_ids[-1] not in saved_covers:
                unsaved_covers.append(cover_ids[-1])

        # fetch unsaved covers
        if len(unsaved_covers) != 0:
            for unsaved_cover in unsaved_covers:
                fetchCovers(unsaved_cover)
    elif SECTIONS.CURRENT_SECTION == SECTIONS.EXPLORE: 
        # current section is set to SECTIONS.EXPLORE the explore section is displayed
        book_names, cover_ids, published_years, authors, edition_counts = fetchBooksForExplore()

        # checking for unsaved covers
        for cover_id in cover_ids:
            if cover_id not in saved_covers:
                unsaved_covers.append(cover_id)

        # fetching unsaved covers
        if len(unsaved_covers) != 0:
            for unsaved_cover in unsaved_covers:
                fetchCovers(unsaved_cover)
    elif SECTIONS.CURRENT_SECTION == SECTIONS.RECOMMENDATIOS:
        # if current section is set to SECTION.RECOMMENDATIONS the recommendataions sections is shown
        book_names, cover_ids, published_years, authors, edition_counts = fetchBooksForRecomendations()

        # checking for unsaved covers
        for cover_id in cover_ids:
            if cover_id not in saved_covers:
                unsaved_covers.append(cover_id)

        # fetching unsaved covers
        if len(unsaved_covers) != 0:
            for unsaved_cover in unsaved_covers:
                fetchCovers(unsaved_cover)

    return render_template('home_page.html',
                            book_names=book_names,
                              cover_ids=cover_ids, 
                              published_years=published_years, 
                              authors=authors, 
                              edition_counts=edition_counts,
                              sections=SECTIONS.getSections(),
                              current_section=SECTIONS.CURRENT_SECTION,
                              page=popular_page,
                              cart_items_count=getCartItemsCount(),
                              notification_count=getUnreadNotificationCount())

@app.route('/individualproduct_page/<coverId>', methods=["GET", "POST"])
def individualproduct_page(coverId):
    # getting book details
    current_book = db.session.query(Book).filter(Book.coverId == coverId).first()
    # getting current user deatils
    current_user = db.session.query(User).filter(User.email == session['user']).first()
    # checking if current book is added to current user's wishlist
    isFavourite = db.session.query(Wishlist).filter(Wishlist.user_id == current_user.id, Wishlist.cover_id == coverId).first() != None
    # getting all user reviews for current book
    all_reviews = db.session.query(Review).filter(Review.book_id == current_book.id).all()
    
    reviews = {}

    for review in all_reviews:
        
        
        user_name = db.session.query(User).filter(User.id == review.user_id).first().firstName + " " + db.session.query(User).filter(User.id == review.user_id).first().lastName
        
        try:
            reviews[user_name][0].append(review.review)
            reviews[user_name][1].append(review.rating)
        except KeyError:
            reviews[user_name] = [[review.review], [review.rating]]
            


    return render_template("individualproduct_page.html", coverId=coverId, book=current_book, isFavourite=isFavourite, reviews=reviews, cart_items_count=getCartItemsCount(),
                              notification_count=getUnreadNotificationCount())

@app.route('/notification_page', methods=['GET'])
def notification_page():
    userEmail = session['user']
    userNotifications = db.session.query(Notification).filter(Notification.user == userEmail).all()
    print("len(userNotifications) = ", len(userNotifications))
    current_notifications = copy.deepcopy(userNotifications)

    for notification in userNotifications:
        notification.isRead = True
    
    db.session.commit()

    return render_template("notifications_page.html", notifications=current_notifications[::-1], cart_items_count=getCartItemsCount(),
                              notification_count=getUnreadNotificationCount())

@app.route('/settings_page', methods=['GET'])
def settings_page():
    return render_template('settings_page.html')

@app.route('/cart_page', methods=['GET'])
def cart_page():

    cart_items = getCartItems()

    cart_item_names = [db.session.query(Book).filter(Book.id == cart_item.book_id).first().bookName for cart_item in cart_items]
    subtotal = sum([cart_item.total_price for cart_item in cart_items])
    tax = subtotal * 0.1
    total = subtotal + tax
    return render_template('cart_page.html', 
                           cart_items=cart_items,
                           cart_item_names=cart_item_names,
                           subtotal=subtotal,
                           tax=tax,
                           total=total, cart_items_count=getCartItemsCount(),
                              notification_count=getUnreadNotificationCount())

@app.route('/billing_page', methods=["GET"])
def billing_page():
    error = ""

    if "invalid payment method" in set(session.keys()):
        # if invalid payment method is selected during payment error is updated and passed to frontend to diplay available otptiosn to user
        error = "Payment method yet to be added, current only cash on delivery is available"

    return render_template('billing_page.html', cart_items_count=getCartItemsCount(),
                              notification_count=getUnreadNotificationCount(), error=error)

@app.route('/orders_page', methods=['GET'])
def orders_page():
    order_items = db.session.query(Order).filter(Order.user_id == db.session.query(User).filter(User.email==session['user']).first().id).all()[::-1]

    order_item_names = [db.session.query(Book).filter(Book.id == order_item.book_id).first().bookName for order_item in order_items]

    return render_template('orders_page.html', 
                           order_items=order_items,
                           order_item_names=order_item_names, cart_items_count=getCartItemsCount(),
                              notification_count=getUnreadNotificationCount())

@app.route('/wishlist_page', methods=['GET'])
def wishlist_page():

    user_id = db.session.query(User).filter(User.email == session['user']).first().id

    wishlist_products = db.session.query(Wishlist).filter(Wishlist.user_id == user_id).all()

    book_names = []
    book_ids = []

    for wishlist_product in wishlist_products:
        book = db.session.query(Book).filter(Book.coverId == wishlist_product.cover_id).first()
        book_names.append(book.bookName)
        book_ids.append(book.id)


    return render_template('wishlist_page.html', wishlist_products=wishlist_products, book_names=book_names, book_ids=book_ids, cart_items_count=getCartItemsCount(),
                              notification_count=getUnreadNotificationCount())

@app.route('/search_page', methods=['GET'])
def search_page():
    return render_template('search_page.html', cart_items_count=getCartItemsCount(),
                              notification_count=getUnreadNotificationCount())
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

    error = ""
    if password != confirmPassword: # checking if password and confirm password matches
        error = "password dosen't match"
        
    elif userWithEmail != None: # checkign if users mail is unique or not
        error = "User with this email already exist"
    else: # adding user to data base 
        otp = send_notification(email)
        # otp = "0000"

        if otp != -1: # in invalid email is entered otp recived will be -1
            user_id = 0
            if len(User.query.all()) != 0:
                user_id = User.query.all()[-1].id+1

            # if no error is encountered new user is created and added to database
            newUser = User(id=user_id,
                    firstName=firstName,
                    lastName=lastName,
                    email=email,
                    password=password,
                    otp=otp)

            db.session.add(newUser)
            db.session.commit()

            # when user registered temp user is added to session untill user is verified
            session['temp_user'] = email
            sendNotification("You are successfully registed to BOOKQUEST")
            return render_template('verification_page.html', state="unverifed")
        else:
            error = "invalid email"

    # if all the cases fails appropriate error message will be displayed in the registration page
    return render_template('signup_page.html',
                            error=error,
                              firstName=firstName,
                              lastName=lastName,
                              email=email,
                              password=password,
                              confirmPassword=confirmPassword)


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

    
    session.clear() # making sure session doesn't have unwanted data from previous sessions
    
    session['loggedIn'] = True # updating session varaible that indicates user is logged in
    session['user'] = email # assining current user email to current email
    sendNotification("Your login is successfull")
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
        
        session.clear()# clearing the pre-verification session 
         # adding loggedIn and user session variable to post-verification session
        session['loggedIn'] = True
        session['user'] = email

        # notification is added to notification db along with current user id 
        sendNotification("you identity is sucessfully verified")
        sendNotification("Welcome to BOOKQUEST")
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

        sendNotification("your password successfully updated")
        return redirect('/login_page')
    else: # if passwords mis-match error message will be displayed
        return render_template('forgot_password_page.html', state='invalid')

# logout route, removes current user form flask session and redirects to loginpage
@app.route('/logout', methods=['GET'])
def logout():
    # change loggeIn state from True to False
    session['loggedIn'] = False
    # removes user from current session there by logging current user out.
    session.pop('user')

    return redirect('/login_page')

# next page route is accessed when user clicks next page button form pages that have paging functionality
@app.route('/nextPageClicked/<section>', methods=['GET', 'POST'])
def nextPageClicked(section):
    global explore_page, recommendation_page, popular_page, search_page_number

    
    if section == SECTIONS.POPULARP_PRODUCTS: # handels next page clicks from popular products section
        if popular_page != 1:
            popular_page = 2
    elif section == SECTIONS.EXPLORE: # handels next page clicks from explore section
        explore_page += 1
    elif section == SECTIONS.RECOMMENDATIOS: # handels next page clicks from recommendation section
        book_recommendations= db.session.query(Book).order_by(Book.editionCount.desc()).all() 
        recommendation_page_count = len(book_recommendations) // ITEMS_IN_PAGE

        if len(book_recommendations) % ITEMS_IN_PAGE != 0:
            recommendation_page_count += 1

        if recommendation_page <  recommendation_page_count:
            recommendation_page += 1
    elif section.split('-')[0] == 'search': # handels next page clicks from search results page
        search_query = section.split('-')[1]

        searchBy = {"book": {'q': search_query}}
        book_names, cover_ids, published_years, authors, edition_counts = search(searchBy=searchBy)
        if len(book_names) > search_page_number * ITEMS_IN_SEARCH_PAGE:
            search_page_number += 1

        return redirect(url_for('search_clicked', search=search_query))

    return redirect('/home_page')

# previous page clicked route: handels previous page button clicks from pages that have paging functionality
@app.route('/prevPageClicked/<section>', methods=['GET', 'POST'])
def prevPageClicked(section):
    global explore_page, recommendation_page, popular_page, search_page_number

    if section == SECTIONS.POPULARP_PRODUCTS: # handels previous page clicks from popular products section
        if popular_page == 3:
            popular_page = 2
        
        elif popular_page == 2:
            popular_page = 1
    elif section == SECTIONS.EXPLORE: # handels previous page clicks from explore sections
        if explore_page - 1 != 0:
            explore_page -= 1
    elif section == SECTIONS.RECOMMENDATIOS: # handels previous page clicks from recommendations sections
        if recommendation_page - 1 != 0:
            recommendation_page -= 1
    elif section.split('-')[0] == 'search': # handels previous page clicks from search results page
        search_query = section.split('-')[1]
        if search_page_number != 1:
            search_page_number -= 1

        return redirect(url_for('search_clicked', search=search_query))

    return redirect('/home_page')

# section clicked route: updates current section in home page, based on selection made by user
@app.route('/sectionClicked/<section>', methods=['GET', 'POST'])
def sectionClicked(section):

    SECTIONS.CURRENT_SECTION = section

    return redirect('/home_page')

# add to cart route: handel request form individual product page, when users wants to add a book to cart
@app.route('/add_to_cart/<book_id>', methods=['GET', 'POST'])
def add_to_cart(book_id):
    user_id = db.session.query(User).get(session['user']).id

    # if book already in cart increase quantity
    cart_item = db.session.query(CartItem).filter(and_(CartItem.book_id == book_id, CartItem.user_id == user_id)).first()

    if cart_item != None:
        cart_item.quantity = cart_item.quantity + 1
        cart_item.total_price = cart_item.quantity * cart_item.price

        db.session.commit()
    else: # else create a new cart item
        cart_item_id = 0

        if len(db.session.query(CartItem).all()) != 0:
            cart_item_id = db.session.query(CartItem).all()[-1].id+1

        new_cart_item = CartItem(id=cart_item_id,
                                book_id=book_id,
                                user_id=user_id,
                                price=30.0,
                                quantity=1,
                                total_price=30.0)
        db.session.add(new_cart_item)
        db.session.commit()

    return redirect('/cart_page')

# remove item from cart: it handels user request to remove current book from cart
@app.route('/remove_item_from_cart', methods=['GET', 'POST'])
def remove_item_from_cart():
    item_id = request.form.get('item_id')

    # deletes respective book form cartItem db
    db.session.delete(db.session.query(CartItem).get(item_id))
    db.session.commit()

    return redirect('/cart_page')

# update quantity route: handels user request to increase or decrease the quantity of book in cart
@app.route('/update_quantity', methods=['GET', 'POST'])
def update_quantity():
    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity'))

    cart_item = db.session.query(CartItem).filter(CartItem.id == item_id).first()
    cart_item.quantity = quantity # updates quantity 
    cart_item.total_price = quantity * cart_item.price # updates price according to change in quqntity

    db.session.commit()

    return redirect('/cart_page')

# make payemnt route: handels user request to make payment and palces the order upon success
# current only cash on delivery is implemented
@app.route('/make_payment', methods=['GET', 'POST'])
def make_payment():
    user_id = db.session.query(User).get(session['user']).id
    books_in_cart = db.session.query(CartItem).filter(CartItem.user_id == user_id)
    payment_type = request.form.get('payment type')

    if payment_type == 'option4': # option 4 is cash on delivey
        # handel cash on delivery orders

        # order success notification is added to notification db for current user
        sendNotification("Your Order is placed")
        for book_in_cart in books_in_cart:
            order_id = 0

            if len(db.session.query(Order).all()) != 0:
                order_id = db.session.query(Order).all()[-1].id+1

            new_order = Order(id=order_id,
                              user_id=book_in_cart.user_id,
                              book_id=book_in_cart.book_id,
                              quantity=book_in_cart.quantity,
                              price=book_in_cart.total_price,
                              status="order being packed")
            
            # order status notification is added to db
            sendNotification(f"{db.session.query(Book).filter(Book.id==book_in_cart.book_id).all()[0].bookName} : {new_order.status}")
            db.session.add(new_order)
            db.session.delete(book_in_cart)
            db.session.commit()
    else:
        # other payment methods are yet to be implemented
        session['invalid payment method'] = True # if payment methods not implemented are selected a flag is added to session
        return redirect('/billing_page')

    return redirect('/home_page')

# add to wishlist route: handel user request from individual product page to add current book to wishlist 
@app.route('/add_to_wishlist/<cover_id>')
def add_to_wishlist(cover_id):
    wishlist_id = 0

    # create wishlist id that do not conflict with existing items in wishlist
    if len(db.session.query(Wishlist).all()) != 0:
        wishlist_id = db.session.query(Wishlist).all()[-1].id+1

    current_user = db.session.query(User).filter(User.email == session['user']).first()

    #  new wishlist item is created and added to db
    new_wishlist_product = Wishlist(id=wishlist_id, user_id=current_user.id, cover_id=cover_id)
    
    db.session.add(new_wishlist_product)
    db.session.commit()

    return redirect(url_for('individualproduct_page', coverId=cover_id))

# remove from wishlist route: handels user requests from individual product page and wishlist page to remove current book from wishlist
@app.route('/remove_from_wishlist/<cover_id>/<page>')
def remove_from_wishlist(cover_id, page):

    current_user = db.session.query(User).filter(User.email == session['user']).first()

    product_in_wishlist = db.session.query(Wishlist).filter(Wishlist.user_id == current_user.id, Wishlist.cover_id == cover_id).first()
    
    db.session.delete(product_in_wishlist)
    db.session.commit()


    if page == "individual product page": # handel remove from wishlist request from indivdual product page
        return redirect(url_for('individualproduct_page', coverId=cover_id))
    else: # handel remove from wishlist request from wishlist page
        return redirect("/wishlist_page")

# search clicked route : handels search request generated by user when go button is clicked
# featches search data add displays those books in search page
@app.route('/search_clicked', methods=['GET', 'POST'])
def search_clicked():
    global saved_covers, search_page_number

    update_saved_covers()
    search_term = request.form.get('search') # collect search team from frontend 

    if search_term == None:
        search_term = request.args.get('search')

    # caputres modified search data retured form helper function "search"
    book_names, cover_ids, published_years, authors, edition_counts = search(searchBy={"book": {'q': search_term}})

    unsaved_covers = []
    book_names = book_names[(search_page_number-1)*ITEMS_IN_SEARCH_PAGE:search_page_number*ITEMS_IN_SEARCH_PAGE]
    cover_ids = cover_ids[(search_page_number-1)*ITEMS_IN_SEARCH_PAGE:search_page_number*ITEMS_IN_SEARCH_PAGE]
    authors = authors[(search_page_number-1)*ITEMS_IN_SEARCH_PAGE:search_page_number*ITEMS_IN_SEARCH_PAGE]

    # checkes if the covers already exists
    for cover_id in cover_ids:
        if cover_id not in saved_covers:
            unsaved_covers.append(cover_id)

    # if covers doesnt exist fetches those covers
    if len(unsaved_covers) != 0:
        for unsaved_cover in unsaved_covers:
            fetchCovers(unsaved_cover)

    return render_template('search_page.html', book_names=book_names, cover_ids=cover_ids, authors=authors, search_term=search_term, cart_items_count=getCartItemsCount(),
                              notification_count=getUnreadNotificationCount())

# review submmited route: handels book reivew submitions made by user
@app.route('/review_submited/<cover_id>', methods=['GET', 'POST'])
def review_submited(cover_id):
    # fetches user and book information
    user_id = db.session.query(User).filter(User.email == session['user']).first().id
    book_id = db.session.query(Book).filter(Book.coverId == cover_id).first().id
    # fetches user review form forntend
    rating = request.form['rating']
    review = request.form['review']

    review_id = 0

    # create a review id with confilicting with existign review ids
    if len(db.session.query(Review).all()) != 0:
        review_id = db.session.query(Review).all()[-1].id+1

    new_review = Review(id=review_id, user_id=user_id, book_id=book_id, rating=rating, review=review)

    db.session.add(new_review)
    db.session.commit()

    return redirect(url_for('individualproduct_page', coverId=cover_id))
################################## helper functions #################################

# used to send verification mail to user during registration
def send_notification(userEmail):
    verification_code = str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9)) 

    message = "Subject: BookQuest Verifcation Code\n\nyour verification code is " + verification_code + "." 

    # try block cathces error when an invalid email is given by user during registration
    try:

        with smtplib.SMTP('smtp.office365.com', 587) as connection:
            connection.starttls()
            connection.login(user=os.getenv('EMAIL'), password=os.getenv('PASSWORD'))
            connection.sendmail(from_addr=os.getenv('EMAIL'), to_addrs=userEmail,
                                msg=message)
            
    except:
        # updates verificaion code to -1 when user enters invalid email which will be caught by try block
        verification_code = -1
        
    return verification_code
    
# search fucntion: searches open library api using its search end point
def search(searchBy):
    # search end point works for seraching by name or by quering by page numnber

    itemType = list(searchBy.keys())[0] # capturing search type
    searchQuery = list(searchBy.values())[0]
    searchTerm = ""

    if itemType == 'book': # based on item type search query is converted to serach term
        searchTerm = searchQuery['q']
    else:
        searchTerm = str(searchQuery)

    # searching search data based to check if the search query is already made
    searchItem = Search.query.filter_by(searchTerm=searchTerm).first()


    if searchItem != None: # if serach is previous made fetches that search data and returns that data
        bookResults = [db.session.query(Book).filter(Book.id == book_search_item.book_id).first() for book_search_item in db.session.query(book_search).filter(book_search.search_id == searchItem.id).all()]

        book_names = [bookResult.bookName for bookResult in bookResults]
        cover_ids = [bookResult.coverId for bookResult in bookResults]
        published_years = [bookResult.publishedYear for bookResult in bookResults]
        authors = [bookResult.author for bookResult in bookResults]
        edition_counts = [bookResult.editionCount for bookResult in bookResults]

        return book_names, cover_ids, published_years, authors, edition_counts



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

    # Get a list of book names.
    book_names = []
    cover_ids = []
    published_years = []
    authors = []
    edition_counts = []

    for book in books:
        
        if 'cover_i' in book:
            book_names.append(book['title'])
            cover_ids.append(book['cover_i'])  
            current_book_publish_year = 0
            if 'publish_year' in book:
                current_book_publish_year = int(book['publish_year'][0])

            published_years.append(current_book_publish_year)
            try:
                authors.append(book['author_name'][0])
            except KeyError:
                authors.append("no author")
            
            edition_counts.append(int(book['edition_count']))

            # if book already exist in table just create new association with search
            existingBook = db.session.query(Book).filter(Book.bookName == book['title']).first()

            if existingBook != None:
                new_book_search = book_search(id=len(book_search.query.all())+1,book_id=existingBook.id, 
                            search_id=searchItem.id)
                db.session.add(new_book_search)
            else: # else create new book and then create association with search
                newBook = Book(id=len(Book.query.all())+1,
                               bookName=book['title'],
                               coverId=book['cover_i'], 
                               publishedYear=current_book_publish_year,
                               author=authors[-1],
                               editionCount=int(book['edition_count']))
                db.session.add(newBook)
                
                new_book_search = book_search(id=len(book_search.query.all())+1, book_id=newBook.id, 
                            search_id=searchItem.id)
                
                db.session.add(new_book_search)
            
            db.session.commit()

    return book_names, cover_ids, published_years, authors, edition_counts

# featch books for explore function: fetches books for explore section
def fetchBooksForExplore():
    global explore_page
    url = 'http://openlibrary.org/search.json'


    params = {
    "q": "*",
    "limit": ITEMS_IN_PAGE,
    "page": explore_page
    }
    
    return search({'all_books': params})  

# featch books for recommendataions: fetches books for recomendations section
def fetchBooksForRecomendations():
    global recommendation_page

    book_recommendations = db.session.query(Book).order_by(Book.editionCount.desc()).all()[(recommendation_page-1)*ITEMS_IN_PAGE:recommendation_page*ITEMS_IN_PAGE]
    book_names = []
    cover_ids = []
    published_years = [] 
    authors = [] 
    edition_counts = []
    
    for book_recommendation in book_recommendations:
        book_names.append(book_recommendation.bookName)
        cover_ids.append(book_recommendation.coverId)
        published_years.append(book_recommendation.publishedYear)
        authors.append(book_recommendation.author)
        edition_counts.append(book_recommendation.editionCount)

    return book_names, cover_ids, published_years, authors, edition_counts

# fecth covers fucntion: given the list of coverid, it querris those covers form open library api
def fetchCovers(cover_ids):
    cover_ids = [cover_ids]
    for cover_id in cover_ids:


        cover_image_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        
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

        # Save the cover image to a cover folder.
        with open(os.path.join(image_directory, f"{cover_id}.jpg"), 'wb') as f:
            f.write(response.content)

        update_saved_covers()

# get saved covers fucntion: fetches all the saved cover id's and return as as list
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

# gets all the saved covers and updated saved_covers vaiable that keeps track of saved covers
def update_saved_covers():
    global saved_covers

    saved_covers = set(getSavedCovers('static/covers'))

# sendNotification fuction: add a new notification instance to user notification databse 
def sendNotification(msg):
    userEmail = None

    if 'temp_user' in set(session.keys()):# handels user notification when user is in temp user stage i.e during registration
        userEmail = session['temp_user']
    else: # handels user notification after user is successfully verified
        userEmail = session['user']
        
    newNotification = Notification(
        id=len(Notification.query.all())+1, 
        user=userEmail, 
        text=msg,
        isRead=False)
    
    db.session.add(newNotification)
    db.session.commit()

# get cart items  fucntion: return all the items in cart for the current logged in user
def getCartItems():
    user_id = db.session.query(User).get(session['user']).id
    cart_items = db.session.query(CartItem).filter(CartItem.user_id == user_id).all()

    return cart_items

# get cart items count function: return count of all cart items of current user in cart database 
def getCartItemsCount():
    return len(getCartItems())

# returns all the unread notification count for current user
def getUnreadNotificationCount():
    unread_notifications = db.session.query(Notification).filter(Notification.user == session['user'], Notification.isRead == False).all()

    return len(unread_notifications)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=3000)