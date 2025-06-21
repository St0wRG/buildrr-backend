import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_mail import Mail
from src.models.user import db
from src.routes.user import user_bp
from src.routes.quote import quote_bp
from src.routes.contact import contact_bp
from src.routes.admin import admin_bp
from src.routes.dashboard import dashboard_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configuration Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'contact@buildrr.fr'
app.config['MAIL_PASSWORD'] = 'your_app_password'  # À remplacer par un vrai mot de passe d'application
app.config['MAIL_DEFAULT_SENDER'] = 'contact@buildrr.fr'

# Enable CORS for all routes
CORS(app)

# Initialize Mail
mail = Mail(app)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(quote_bp, url_prefix='/api')
app.register_blueprint(contact_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

