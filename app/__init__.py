import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_mail import Mail
from dotenv import load_dotenv
from flask_wtf.csrf import generate_csrf
from flask_login import LoginManager

# Cargar variables de entorno desde .env
load_dotenv()

# Inicialización de extensiones globales
db = SQLAlchemy()
bcrypt = Bcrypt()
csrf = CSRFProtect()
mail = Mail()
login_manager = LoginManager()

def crear_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    csrf.init_app(app)

    # Configuración adicional desde variables de entorno
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')  # <<-- ¡Muy importante para emails!

    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("La variable de entorno 'SQLALCHEMY_DATABASE_URI' no está definida. Configúrala en .env.")

    # Inicializar extensiones
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    # Importar modelos y rutas después de inicializar las extensiones
    from app.modelos import Usuario
    from app.rutas import main
    app.register_blueprint(main)

    # CSRF token en Jinja
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf())

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    return app

app = crear_app()
