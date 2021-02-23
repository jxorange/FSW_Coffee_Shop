import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth
import ssl
'''
solve certificate verify failed
'''
ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES

'''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['GET'])
def get_drinks():
    selection = Drink.query.order_by(Drink.id).all()
    drinks = [drink.short() for drink in selection]

    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200


'''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    selection = Drink.query.order_by(Drink.id).all()
    drinks = [drink.long() for drink in selection]

    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200


'''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(jwt):
    try:
        body = request.get_json()
        req_title = body.get('title', None)
        req_recipe = json.dumps(body.get('recipe', None))

        drink = Drink(title=req_title, recipe=req_recipe)
        drink.insert()

        return jsonify({
            'success': True,
            'drink': [drink.long()]
        }), 200

    except Exception as e:
        abort(422)


'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, drink_id):
    """PATCH /drinks/<id>

    An endpoint that updates the corresponding row for <id>. Requires the
    'patch:drinks' permission.

    Args:
        jwt: a json web token (string).
        drink_id: where <drink_id> is the existing model id (int).

    Returns:
        A status code 200 and json {"success": True, "drinks": drink} where
        drink is an array containing only the updated drink in the drink.long()
        representation or appropriate status code indicating reason for
        failure.
    """
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

        if drink is None:
            abort(404)

        body = request.get_json()
        req_title = body.get('title', drink.title)
        req_recipe = json.dumps(body.get('recipe', drink.recipe))

        drink.title = req_title
        drink.recipe = req_recipe
        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200

    except Exception as e:
        abort(422)


'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, drink_id):
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

        if drink is None:
            abort(404)

        id = drink.id
        drink.delete()

        return jsonify({
            'success': True,
            'delete': id
        }), 200

    except Exception as e:
        abort(422)


## Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
    error handler should conform to general task above 
'''


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
    }), 404


'''
    error handler should conform to general task above 
'''


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized"
    }), 401
