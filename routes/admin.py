from flask import Blueprint, render_template
from models.models import User

admin_route = Blueprint('Admin', __name__)

admin_route.route('/')
def admin_page():

    
    return render_template('CadastroUsuarios.html')