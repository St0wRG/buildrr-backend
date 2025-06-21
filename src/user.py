from flask import Blueprint, request, jsonify
from src.models.user import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

user_bp = Blueprint('user', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, 'asdf#FGSgvasgf$5$WGT', algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@user_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        # Créer un nouvel utilisateur
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            first_name=data['firstName'],
            last_name=data['lastName'],
            email=data['email'],
            password=hashed_password,
            company=data.get('company', ''),
            phone=data.get('phone', '')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Générer un token
        token = jwt.encode({
            'user_id': new_user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, 'asdf#FGSgvasgf$5$WGT', algorithm='HS256')
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user': {
                'id': new_user.id,
                'firstName': new_user.first_name,
                'lastName': new_user.last_name,
                'email': new_user.email,
                'company': new_user.company
            }
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password, data['password']):
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, 'asdf#FGSgvasgf$5$WGT', algorithm='HS256')
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user.id,
                    'firstName': user.first_name,
                    'lastName': user.last_name,
                    'email': user.email,
                    'company': user.company
                }
            }), 200
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'user': {
            'id': current_user.id,
            'firstName': current_user.first_name,
            'lastName': current_user.last_name,
            'email': current_user.email,
            'company': current_user.company,
            'phone': current_user.phone,
            'memberSince': current_user.created_at.isoformat() if current_user.created_at else None
        }
    }), 200

