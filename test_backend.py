import pytest
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