import pytest
from flask import Flask
from main import app, db, User
# @pytest.mark.parametrize("input,expected", [
#     ({"firstName"},)
# ])

@pytest.fixture(scope='module')
def test_client():
    flask_app = app # the Flask app instance 
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # this makes the test client available to tests

    ctx.pop()

def test_signup(test_client):
    form_data = {'firstName': 'test', 'lastName': 'test', 'email': 'janardhankarriavula@gmail.com', 'password': 'test', 'confirmPassword': 'test'}
    response = app.test_client().post('/register', data=form_data)
    
    with app.app_context():
        registered_user = db.session.get(User, form_data['email'])
        assert registered_user.firstName == form_data['firstName']
        db.session.delete(registered_user)

        db.session.commit()


def test_login(test_client):
    form_data = {'email': 'test', 'password': 'test'}

    response = test_client.post('/login', data=form_data)

    with test_client.session_transaction() as session:
        assert session['loggedIn'] == True 

def test_update_password(test_client):
    form_data = {'password': 'testnew', 'confirmPassword': 'testnew'}
    forgot_email = 'test'
    old_password = 'test'

    with test_client.session_transaction() as session:
        session['forgot email'] = forgot_email

    response = test_client.post('/update_password', data=form_data)

    with app.app_context():
        registered_user = db.session.get(User, forgot_email)
        assert registered_user.password == form_data['password']

        registered_user.password = old_password

        db.session.commit()

    def client():
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_next_page_clicked_popular_page_1(client):
        response = client.get('/nextPageClicked/POPULARP_PRODUCTS')
        
        # Ensure the route redirects to '/home_page'
        assert response.status_code == 302
        assert response.location == 'http://localhost/home_page'
    
    def test_next_page_clicked_invalid_section(client):
        response = client.get('/nextPageClicked/INVALID_SECTION')

        # Ensure the route returns a 404 status code for an invalid section
        assert response.status_code == 404
    def test_logout(test_client):
         response = test_client.get('/logout')
         with test_client.session_transaction() as session:
              assert session['loggedIn'] == False
    def test_verification_route(test_client):
            with test_client.session_transaction() as sess:
                sess['otp'] = '123456'  # Sample OTP to test
            response = test_client.get('/verifcation_page')
            assert response.status_code == 200
            assert b"Email Verification" in response.data
    def test_login_route(test_client):
            response = test_client.get('/login_page')
            assert response.status_code == 200
            assert b"Login" in response.data
    def test_signup_route(test_client):
            response = test_client.get('/signup_page')
            assert response.status_code == 200
            assert b"Sign Up" in response.data
