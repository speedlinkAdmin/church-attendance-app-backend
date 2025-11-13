from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

import json
from flask.json import JSONEncoder

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, type(...)):  # Handle ellipsis
            return None
        return super().default(obj)
    
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
