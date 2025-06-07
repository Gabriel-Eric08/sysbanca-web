from flask import Blueprint, render_template
from util.checkCreds import checkCreds

home_route = Blueprint('Home', __name__)

@home_route.route('/')
def home():
    check_creds = checkCreds()
    if check_creds['success'] == True:
        return render_template('principal.html')
    else:
        return check_creds['message']