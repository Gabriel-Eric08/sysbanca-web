from flask import Flask, Blueprint, jsonify
from models.models import Usuario

users_route = Blueprint('Users', __name__)

@users_route.route('/', methods=['GET'])
def list_users():
    usuarios = Usuario.query.all()
    return jsonify([
        {"id": u.id, "nome": u.nome} for u in usuarios
    ])