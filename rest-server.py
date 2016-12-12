#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask.ext.httpauth import HTTPBasicAuth
import sqlite3
import json
from flask import g

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3 as lite
import sys
import pylab
from scipy.fftpack import rfft, irfft, fftfreq
import math
import matplotlib.pyplot as pp

DATABASE = 'sqlite-database/csciApp.db'
print DATABASE


############
# Function Definitions for Heartrate
######
def common_elements(list1, list2):
    result = []
    for element in list1:
        if element in list2:
            result.append(element)
    return result
    
def merge_arrays(array, array2):
    for i in range(0,len(array2)):
        array = find_nearest(array,array2[i],5)
    return common_elements(array2,array)

def merge_nearest(array):
    for i in range(0,len(array)):
        array = find_nearest(array,array[i],10)
    return np.unique(array)

def find_nearest(array,value,wsize):
    idx = (np.abs(array-value)<=wsize)
    array[idx] = value
    return array

outliers = 0.025
threshTop = 0.45
threshBot = -0.45
def findHeartRate(v):
    dv = np.gradient(v)
    dv[dv>outliers] = outliers
    dv[dv<-outliers] = -outliers
    norm = np.array([float(d)/max(dv) for d in dv])
    
    pulses = norm.copy()
    pulses[pulses<threshBot] = -1
    pulses[pulses>threshTop] = 1
    pulses[abs(pulses)!=1] = 0
    
    top = np.where(pulses==1)[0]
    top = merge_nearest(top.copy())
    bot = np.where(pulses==-1)[0]
    bot = merge_nearest(bot.copy())
    intersect = merge_arrays(top.copy(),bot.copy())
        
    return len(intersect) ##len(top),  len(bot), 

def calculateHR(v,dtarray):
    dt = np.mean(dtarray)/1000.0
    secs = len(v)*dt
    perMin = secs/60.0
    print "{0} items".format(len(v))
    print "{0} Seconds, {1} dt, {2} PerMin".format(secs, dt, perMin)
    count = findHeartRate(v)
    rate = count/perMin
    print "{0} BPM".format(rate)
    return rate

############


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
    
    
@app.route('/api/v1.0/heartrate/<int:user_id>', methods = ['POST'])
def calculateHeartrateForUser(user_id):        
    v = request.json.get('values', "")
    dtarray = request.json.get('dt', "")
    bpm = calculateHR(v,dtarray)
    query = "INSERT INTO history (user, rateType, recordedValue)  VALUES (?,'heart',?);"
    query_db(query, ( user_id, bpm))
    return make_response(jsonify( { 'heartrate': bpm } ), 201)

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
