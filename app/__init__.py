from flask import Flask
from config import Config
from .extensions import db, migrate, jwt, cors, CustomJSONProvider
from .routes import register_routes
import logging 
from flask import jsonify
from flasgger import Swagger
from app.tasks.scheduler import start_scheduler

def setup_roles_on_startup(app):
    """Automatically setup roles when the app starts."""
    with app.app_context():
        from .models.user import Role, User
        from .extensions import db
        
        # Check if setup is already done
        if Role.query.filter_by(name='Super Admin').first():
            return  # Setup already done
        
        print("Setting up roles...")
        
        # Create roles
        roles_data = {
            "Super Admin": "Full system administrator with access to everything",
            "State Admin": "Administrator for a specific state", 
            "Region Admin": "Administrator for a specific region",
            "District Admin": "Administrator for a specific district",
            "Group Admin": "Administrator for a specific group", 
            "Viewer": "Read-only access"
        }
        
        for role_name, description in roles_data.items():
            role = Role(name=role_name, description=description)
            db.session.add(role)
        
        db.session.commit()
        print("Roles setup complete!")


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    

    

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    # cors.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})
    app.json_encoder = CustomJSONProvider(app)

    setup_roles_on_startup(app)
    start_scheduler()


     # Initialize Swagger
    # Initialize Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,  # include all endpoints
                "model_filter": lambda tag: True,  # include all models
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs/",  # Swagger UI location
    }

    template = {
        "swagger": "2.0",
        "info": {
            "title": "PARADOX API",
            "description": "Powering organizational intelligence with precision — PARADOX backend services and API documentation.",
            "version": "1.0.0",
            "contact": {
                "name": "PARADOX Dev Team",
                "email": "support@paradox.io"
            },
            "license": {
                "name": "MIT License"
            },
        },
        "basePath": "/",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
            }
        }
    }

    Swagger(app, config=swagger_config, template=template)

    # register routes/blueprints
    register_routes(app)

     # -------------------------------
    # 💠 Base route for your brand
    # -------------------------------
    @app.route("/")
    def index():
        """
        Welcome message for the PARADOX API.
        """
        return jsonify({
            "brand": "PARADOX",
            "message": "All HAil Paradox — Empowering Data, People & Intelligence.",
            "docs_url": "/docs/",
            "status": "running ✅"
        }), 200

    # simple root for quick health-check
    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

        # global JWT expired handler (example)
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"msg": "token expired"}), 401
    
    return app
