#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask.ext.httpauth import HTTPBasicAuth
import sqlite3
import json
from flask import g

DATABASE = 'sqlite-database/csciApp.db'
print DATABASE


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def query_db(query, args=()):
	connection = sqlite3.connect(DATABASE)
	connection.row_factory = dict_factory
	cursor = connection.cursor()
	cursor.execute(query,args)
	connection.commit()
	results = cursor.fetchall()
	cursor.close()
	return results

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

app = Flask(__name__, static_url_path = "")
auth = HTTPBasicAuth()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_csciAppDev', None)
    if db is not None:
        db.close()

@auth.get_password
def get_password(username):
    if username == 'miguel':
        return 'python'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify( { 'error': 'Unauthorized access' } ), 403)
# return 403 instead of 401 to prevent browsers from displaying the default auth dialog

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)
    
@app.route('/dev/api/motiondata', methods = ['POST'])
def save_testdata():
    query = "INSERT INTO MotionData_dev (xAxis, yAxis, zAxis, timeStep) VALUES (?,?,?,?);"
    query_db(query, (request.json.get('x', ''), 
    				 request.json.get('y', ''),
    				 request.json.get('z', ''),
    				 request.json.get('t', '')))
    return make_response(jsonify( { 'success': True } ), 201)
    
@app.route('/todo/api/v1.0/tasks', methods = ['GET'])
@auth.login_required
def get_tasks():
    tasks = query_db('select * from users;')
    return jsonify( { 'tasks': tasks } )

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods = ['GET'])
@auth.login_required
def get_task(task_id):
    task = query_db('select * from users where id=?;',[task_id])
    return jsonify( { 'task': task } )

@app.route('/todo/api/v1.0/tasks', methods = ['POST'])
@auth.login_required
def create_task():
    if not request.json or not 'title' in request.json:
        abort(400)
    task = {
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': 0
    }
    query = "INSERT INTO users (title, description, done) VALUES (?,?,0);"
    query_db(query, (request.json.get('title', ""), request.json.get('description', "")))
    return jsonify( { 'task': task } ), 201

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods = ['PUT'])
@auth.login_required
def update_task(task_id):        
    query = "UPDATE users SET title = ?, description = ?, done = ? WHERE ID = ?;"
    query_db(query, ( request.json.get('title', ""), request.json.get('description', ""), request.json.get('done'), task_id ))
    task = query_db('select * from users where id=?;',[task_id])
    return jsonify( { 'task': task } )

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods = ['DELETE'])
@auth.login_required
def delete_task(task_id):
    query = "DELETE FROM users WHERE ID = ?;"
    query_db(query, [task_id])
    return jsonify( { 'result': True } )

if __name__ == '__main__':
    app.run(debug = True,host='0.0.0.0')
