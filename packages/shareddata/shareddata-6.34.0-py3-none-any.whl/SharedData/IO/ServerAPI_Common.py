"""
Common imports, variables, and functions shared across ServerAPI modules.
"""

# Flask imports
from flask import Flask, Response, g, request, jsonify, make_response
from flasgger import Swagger, swag_from
from werkzeug.middleware.proxy_fix import ProxyFix

# Data handling imports
import bson
from bson import json_util
from bson.objectid import ObjectId
import pymongo
import lz4.frame as lz4f
import pandas as pd
import numpy as np

# Standard library imports
import os
import datetime
import gzip
import json
import time
from collections import defaultdict
import threading
from pathlib import Path
import random

# SharedData imports
from SharedData.SharedData import SharedData
from SharedData.Logger import Logger
from SharedData.Database import *
from SharedData.CollectionMongoDB import CollectionMongoDB
from SharedData.Routines.WorkerPool import WorkerPool

# Global SharedData instance
shdata = SharedData('SharedData.IO.ServerAPI', user='master', quiet=True)

# Configuration constants
MAX_RESPONSE_SIZE_BYTES = int(20*1024*1024)

# Flask app configuration
app = Flask(__name__)
app.config['APP_NAME'] = 'SharedData API'
app.config['FLASK_ENV'] = 'production'
app.config['FLASK_DEBUG'] = '0'

if not 'SHAREDDATA_SECRET_KEY' in os.environ:
    raise Exception('SHAREDDATA_SECRET_KEY environment variable not set')

app.config['SECRET_KEY'] = os.environ['SHAREDDATA_SECRET_KEY']
app.config['SWAGGER'] = {
    'title': 'SharedData API',
    'uiversion': 3
}

docspath = 'ServerAPIDocs.yml'
swagger = Swagger(app, template_file=docspath)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Thread-safe in-memory storage for traffic statistics
traffic_stats = {
    'total_requests': 0,
    'endpoints': defaultdict(lambda: {
        'requests': 0,
        'total_response_time': 0.0,
        'status_codes': defaultdict(int),
        'total_bytes_sent': 0,
        'total_bytes_received': 0  
    })
}

traffic_rates = {
    'last_total_requests': 0,
    'last_total_bytes_sent': 0,
    'last_total_bytes_received': 0,  
    'last_timestamp': time.time()
}

# Lock for thread-safe updates to traffic_stats
stats_lock = threading.Lock()

# Lock for updating users data
users_lock = threading.Lock()
users = {}

# User dictionary to store user data by token
with users_lock:
    if users == {}:
        user_collection = shdata.collection('Symbols', 'D1', 'AUTH', 'USERS', user='SharedData')
        _users = list(user_collection.find({}))  # Ensure we can iterate multiple times
        new_tokens = {user['token'] for user in _users}
        # Add or update users
        for user in _users:
            if user['token'] not in users:
                users[user['token']] = user
            else:
                users[user['token']].update(user)
        # Remove users not present in the new list
        tokens_to_delete = [token for token in users if token not in new_tokens]
        for token in tokens_to_delete:
            del users[token]        

def check_permissions(reqpath: list[str], permissions: dict, method: str) -> bool:
    """
    Check if a given request path and HTTP method are permitted based on a nested permissions dictionary.
    
    This function iteratively traverses the permissions tree according to the segments in reqpath.
    It supports wildcard segments ('*') and checks if the specified method is allowed at the final node.
    Returns True if the method is permitted for the path, otherwise False.
    
    Parameters:
        reqpath (list[str]): A list of path segments representing the requested resource path.
        permissions (dict): A nested dictionary representing permission rules, where keys are path segments or '*',
                            and values are either further nested dicts or lists of allowed methods.
        method (str): The HTTP method (e.g., 'GET', 'POST') to check permission for.
    
    Returns:
        bool: True if the method is permitted for the given path, False otherwise.
    """
    node = permissions
    for segment in reqpath:
        if segment in node:
            node = node[segment]
        elif '*' in node:
            node = node['*']
        else:
            return False
        # If leaf is not dict (wildcard or method list)
        if not isinstance(node, dict):
            if '*' in node or (isinstance(node, list) and method in node):
                return True
            return False
    # At the end, check at current node
    if '*' in node:
        return True
    if method in node:
        return True
    return False

def authenticate(request):    
    """
    Authenticate an incoming HTTP request by validating a token provided via query parameters or custom headers, and verify the user's permissions for the requested resource and HTTP method.
    
    Parameters:
        request (flask.Request): The incoming HTTP request object containing query parameters, headers, path, and method.
    
    Returns:
        bool: True if the token is valid and the user has the required permissions for the requested resource and HTTP method; False otherwise.
    """
    try:
        token = request.args.get('token')  # Not Optional
        if not token:
            token = request.headers.get('X-Custom-Authorization')
        if not token:
            token = request.headers.get('x-api-key')
        
        if not token in users:
            time.sleep(3)
            return False
       
        userdata = users[token]
        
        reqpath = str(request.path).split('/')[1:]
        user = request.args.get('user','master')        
        if user:
            reqpath = [user] + reqpath

        tablesubfolder = request.args.get('tablesubfolder')
        if tablesubfolder:
            reqpath = reqpath + [tablesubfolder]

        permissions = userdata['permissions']
        method = str(request.method).upper()
        
        return check_permissions(reqpath, permissions, method)
    except Exception as e:
        return False
