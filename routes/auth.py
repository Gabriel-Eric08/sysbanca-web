from flask import  Flask, Blueprint, render_template, request, redirect, url_for, flash
from models.models import Extracao
from db_config import db

auth_route = Blueprint('Auth', __name__)

@auth_route.route('/')
def auth_page():

    return render_template('Login.html')

@auth_route.route('/', methods=['POST'])
def auth_login():

    resp = resp.setc