#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        image_url = data.get('image_url')
        bio = data.get('bio')

        # if not username or not password:
        #     return {'message': 'username and password required'}, 400

        user = User(username=username, image_url=image_url, bio=bio)
        user.password_hash = password
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {'message': 'Unprocessable Entity'}, 422
        session['user_id'] = user.id
        return user.to_dict(), 201
class CheckSession(Resource):
    def get(self):
        if session.get('user_id'):
            user = User.query.filter(User.id == session['user_id']).first()
            return user.to_dict(), 200
        return {'message': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        json = request.get_json()
        user = User.query.filter(User.username == json['username']).first()
        if user:
            if user.authenticate(json['password']):
                session['user_id'] = user.id
                return user.to_dict(), 200
        else:
            return {"message":"Incorrect username or password"}, 401

class Logout(Resource):
    def delete(self):
        if session['user_id']:
            session['user_id'] = None
            return {}, 204
        else:
            return {'message': 'Unauthorized'}, 401
        
####################### Protected Routes ########################

@app.before_request
def check_if_logged_in():
    if request.endpoint in ['recipes']:  ### Put protected routes here ###
        if not session['user_id']:
            return {'message':'You must log in to view this content'},401

class RecipeIndex(Resource):
    def get(self):
        recipes = [recipe.to_dict() for recipe in Recipe.query.all()]
        return recipes, 200
    
    def post(self):
        json = request.get_json()
        try:
            recipe = Recipe(
                title = json['title'],
                instructions = json['instructions'],
                minutes_to_complete = json['minutes_to_complete'],
                user_id = session['user_id']
            )
        
            db.session.add(recipe)
            db.session.commit()
            return recipe.to_dict(), 201
        except ValueError as ve:
            return {'message':str(ve)}, 422
        except Exception as e:
            return {'message':str(e)}, 500
        

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)