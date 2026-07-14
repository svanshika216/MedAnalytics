from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app,db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.patients import patients_bp
    from app.routes.appointments import appointments_bp
    from app.routes.pharmacy import pharmacy_bp
    from app.routes.analytics import analytics_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(analytics_bp)

    from app import models
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('shared/403/html'), 403
    
    return app
