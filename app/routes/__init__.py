from .auth_routes import auth_bp
# from .state_routes import state_bp
from .hierarchy_routes import hierarchy_bp
from .user_routes import user_bp
from .attendance_routes import attendance_bp
from .youth_attendance_routes import ya_bp
from .dashboard_routes import dashboard_bp
from .admin_routes import admin_bp
from .attendance_monitor_routes import monitor_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/auth")
    # app.register_blueprint(state_bp, url_prefix="/admin/states")
    app.register_blueprint(hierarchy_bp, url_prefix="/hierarchy")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(attendance_bp, url_prefix="/attendance")
    app.register_blueprint(ya_bp, url_prefix="/youth-attendance")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(monitor_bp, url_prefix="/attendance-monitor")
