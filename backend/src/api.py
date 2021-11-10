import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# CORS Headers


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Headers",
                         "Content-Type,Authorization,true")
    response.headers.add("Access-Control-Allow-Methods",
                         "GET,PUT,POST,DELETE,OPTIONS")
    return response


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UN COMMENTED ON FIRST RUN
!! Running this function will add one
'''
# db_drop_and_create_all()

# ROUTES


@app.route('/drinks', methods=['GET'])
def get_drinks():
    """
     GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    """
    drinks = [drink.short() for drink in Drink.query.all()]
    return jsonify({"success": True, "drinks": drinks})


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-details')
def get_drinks_detail(token):
    """
    GET /drinks-detail
        it should require the 'get:drinks-details' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    """

    try:
        drinks = [drink.long() for drink in Drink.query.all()]
        return jsonify({'success': True, 'drinks': drinks})
    except Exception as ex:
        abort(ex.code)


@app.route('/drinks', methods=['POST'])
@requires_auth('create:drinks')
def add_drink(token):
    """
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'create:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
    where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
    """
    try:
        drink_data = request.get_json()
        drink_title = drink_data.get('title')
        drink_recipe = drink_data.get('recipe')

        if(not (drink_title and drink_recipe)):
            abort(400)

        drink = Drink()
        drink.title = drink_data.get('title')
        drink.recipe = json.dumps(drink_data.get('recipe'))
        drink.insert()
        drinks = [drink.long()]

        return jsonify({'success': True, 'drinks': drinks})
    except Exception as ex:
        abort(ex.code)


@app.route('/drinks/<drink_id>', methods=['PATCH'])
@requires_auth('update:drinks')
def update_drink(token, drink_id):
    """
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'update:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
    where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
    """
    try:
        drink = Drink.query.filter_by(id=drink_id).first()
        if not drink:
            abort(404)

        drink_data = request.get_json()
        drink_data['recipe'] = json.dumps(drink_data.get('recipe'))
        drink_title = drink_data.get('title')
        drink_recipe = drink_data.get('recipe')

        if(not (drink_title and drink_recipe)):
            abort(400)

        drink.title = drink_title
        drink.recipe = drink_recipe
        drink.update()

        drinks = [drink.long()]

        return jsonify({
            'success': True,
            'drinks': drinks
        })
    except Exception as ex:
        abort(ex.code)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    """
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
    """
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if not drink:
            abort(404)
        drink.delete()
    except Exception as ex:
        abort(ex.code)

    return jsonify({'success': True, 'delete': drink.id}), 200


# Error Handling
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


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }),
        404,
    )


@app.errorhandler(405)
def method_not_allowed(error):
    print(error)
    return jsonify({
        "success": False,
        "error": 405,
        "message": 'Method Not Allowed'
    }), 405


@app.errorhandler(500)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal server error"
    }), 500


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code


if __name__ == "__main__":
    app.debug = True
    app.run()
