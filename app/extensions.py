from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from flask.json.provider import JSONProvider
import json

# Custom JSON encoder to handle ellipsis and other non-serializable objects
class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, default=self.default)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

    def default(self, obj):
        # Handle ellipsis
        if isinstance(obj, type(...)):
            return None
        # Handle other non-serializable objects if needed
        # Add more type handlers here if necessary
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
    
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
