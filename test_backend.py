import pytest
from flask import Flask
from main import app, db, User, SECTIONS, explore_page

@pytest.fixture(scope='module')
def test_client():
    flask_app = app # the Flask app instance 
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests.
    ctx = flask_app.app_context()
    ctx.push()

    yield testing_client  # this makes the test client available to tests

    ctx.pop()

@pytest.mark.parametrize("input,expected", [
    (['valid', {'firstName': 'test', 'lastName': 'test', 'email': 'janardhankarriavula@gmail.com', 'password': 'test', 'confirmPassword': 'test'}], 'test'),
    (['invalid email', {'firstName': 'test', 'lastName': 'test', 'email': 'pythontest363@gmail.com', 'password': 'test', 'confirmPassword': 'test'}], "<h1>error message will be displayed, for improper signup deails format</h1>"),
    (['invalid password', {'firstName': 'test', 'lastName': 'test', 'email': 'pythontest364@gmail.com', 'password': 'test', 'confirmPassword': 'test1'}], "<h1>error message will be displayed, for improper signup deails format</h1>"),
])
def test_signup(test_client, input, expected):
    response = app.test_client().post('/register', data=input[1])

    with app.app_context():
        
        if input[0] == 'valid':
            registered_user = db.session.get(User, input[1]['email'])
            assert registered_user.firstName == expected

            db.session.delete(registered_user)

            db.session.commit()
        else:
            assert response.text == expected

        

@pytest.mark.parametrize("input,expected", [
     (['valid', {'email': 'test', 'password': 'test'}], True),
     (['invalid email', {'email': 'test100', 'password': 'test'}], "<h1> user with give email doesn't exist </h1>"),
     (['invalid password', {'email': 'test', 'password': 'test12'}], "<h1> Incorrect password </h1>"),
])
def test_login(test_client, input, expected):

    response = test_client.post('/login', data=input[1])

    with test_client.session_transaction() as session:
        if input[0] == 'valid':
            assert session['loggedIn'] == expected
        else:
            assert response.text == expected 

@pytest.mark.parametrize("input,expected", [
     (["valid", {'password': 'testnew', 'confirmPassword': 'testnew'}, {"forgot email": "test"}, {"old password": "test"}], {"new password": "testnew"}),
     (["password mis-match", {'password': 'testnew', 'confirmPassword': 'testneew'}, {"forgot email": "test"}, {"old password": "test"}], {"old password": "test"}),
])
def test_update_password(test_client, input, expected):

    with test_client.session_transaction() as session:
        session['forgot email'] = input[2]['forgot email']

    response = test_client.post('/update_password', data=input[1])

    with app.app_context():
        registered_user = db.session.get(User, input[2]['forgot email'])
        if input[0] == 'valid':
            assert registered_user.password == expected['new password']

            registered_user.password = input[3]['old password']

            db.session.commit()
        else:
            assert registered_user.password == expected['old password']

        

def test_next_page_clicked(test_client):
    global explore_page
    explore_page_before = explore_page

    response = test_client.post('/nextPageClicked/'+SECTIONS.EXPLORE)

    from main import explore_page

    assert explore_page_before + 1 == explore_page

def test_prev_page_clicked(test_client):
    global explore_page
    explore_page_before = explore_page

    response = test_client.post('/prevPageClicked/'+SECTIONS.EXPLORE)
    
    from main import explore_page

    assert explore_page_before - 1 == explore_page

def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

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

def test_forgot_password_route(test_client):
        response = test_client.get('/forgot_password_page')
        assert response.status_code == 200
        assert b"RESET YOUR PASSWORD" in response.data
        
def test_home_route(test_client):
        response = test_client.get('/')
        assert response.status_code == 200
        assert b"Login" in response.data
