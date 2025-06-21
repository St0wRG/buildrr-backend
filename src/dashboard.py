from flask import Blueprint, request, jsonify
from src.models.user import db, User, Order, PrivateMessage
from src.routes.user import token_required
from werkzeug.security import check_password_hash, generate_password_hash
import random
import string

dashboard_bp = Blueprint('dashboard', __name__)

def generate_order_id():
    """Génère un ID de commande unique"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@dashboard_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        return jsonify({
            'user': current_user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@dashboard_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        data = request.get_json()
        
        # Mise à jour des informations
        if 'firstName' in data:
            current_user.first_name = data['firstName']
        if 'lastName' in data:
            current_user.last_name = data['lastName']
        if 'company' in data:
            current_user.company = data['company']
        if 'phone' in data:
            current_user.phone = data['phone']
        
        # Changement de mot de passe si fourni
        if 'currentPassword' in data and 'newPassword' in data:
            if check_password_hash(current_user.password, data['currentPassword']):
                current_user.password = generate_password_hash(data['newPassword'])
            else:
                return jsonify({'message': 'Current password is incorrect'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@dashboard_bp.route('/orders', methods=['GET'])
@token_required
def get_user_orders(current_user):
    try:
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@dashboard_bp.route('/messages', methods=['GET'])
@token_required
def get_user_messages(current_user):
    try:
        # Messages envoyés par l'utilisateur
        sent_messages = PrivateMessage.query.filter_by(sender_id=current_user.id).order_by(PrivateMessage.created_at.desc()).all()
        # Messages reçus par l'utilisateur
        received_messages = PrivateMessage.query.filter_by(recipient_id=current_user.id).order_by(PrivateMessage.created_at.desc()).all()
        
        return jsonify({
            'sentMessages': [msg.to_dict() for msg in sent_messages],
            'receivedMessages': [msg.to_dict() for msg in received_messages]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@dashboard_bp.route('/messages', methods=['POST'])
@token_required
def send_message_to_admin(current_user):
    try:
        data = request.get_json()
        
        # Trouver l'administrateur
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            return jsonify({'message': 'No admin found'}), 404
        
        # Créer le message
        new_message = PrivateMessage(
            subject=data['subject'],
            message=data['message'],
            sender_id=current_user.id,
            recipient_id=admin.id
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({
            'message': 'Message sent to admin successfully',
            'messageId': new_message.id
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@dashboard_bp.route('/account', methods=['DELETE'])
@token_required
def delete_account(current_user):
    try:
        data = request.get_json()
        
        # Vérifier le mot de passe
        if not check_password_hash(current_user.password, data['password']):
            return jsonify({'message': 'Password is incorrect'}), 400
        
        # Supprimer l'utilisateur (cascade supprimera les commandes et messages)
        db.session.delete(current_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Account deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@dashboard_bp.route('/stats', methods=['GET'])
@token_required
def get_user_stats(current_user):
    try:
        # Statistiques utilisateur
        total_orders = Order.query.filter_by(user_id=current_user.id).count()
        completed_orders = Order.query.filter_by(user_id=current_user.id, status='completed').count()
        pending_orders = Order.query.filter_by(user_id=current_user.id, status='pending').count()
        in_progress_orders = Order.query.filter_by(user_id=current_user.id, status='in-progress').count()
        cancelled_orders = Order.query.filter_by(user_id=current_user.id, status='cancelled').count()
        
        total_spent = db.session.query(db.func.sum(Order.price)).filter_by(user_id=current_user.id, status='completed').scalar() or 0
        
        unread_messages = PrivateMessage.query.filter_by(recipient_id=current_user.id, is_read=False).count()
        
        return jsonify({
            'stats': {
                'totalOrders': total_orders,
                'completedOrders': completed_orders,
                'pendingOrders': pending_orders,
                'inProgressOrders': in_progress_orders,
                'cancelledOrders': cancelled_orders,
                'totalSpent': total_spent,
                'unreadMessages': unread_messages
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@dashboard_bp.route('/quotes', methods=['GET'])
@token_required
def get_user_quotes(current_user):
    try:
        quotes = Quote.query.filter_by(user_id=current_user.id).order_by(Quote.created_at.desc()).all()
        return jsonify({
            'quotes': [quote.to_dict() for quote in quotes]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@dashboard_bp.route('/quotes/<int:quote_id>/respond', methods=['POST'])
@token_required
def dashboard_respond_to_quote(current_user, quote_id):
    try:
        quote = Quote.query.filter_by(id=quote_id, user_id=current_user.id).first()
        if not quote:
            return jsonify({'message': 'Quote not found'}), 404
        
        if quote.status != 'sent':
            return jsonify({'message': 'Quote cannot be responded to in current status'}), 400
        
        data = request.get_json()
        response_type = data.get('response')  # 'accepted' ou 'rejected'
        message = data.get('message', '')
        
        if response_type not in ['accepted', 'rejected']:
            return jsonify({'message': 'Invalid response type'}), 400
        
        # Mettre à jour le devis
        quote.client_response = response_type
        quote.client_response_at = datetime.utcnow()
        quote.client_message = message
        quote.status = 'accepted' if response_type == 'accepted' else 'rejected'
        
        db.session.commit()
        
        return jsonify({
            'message': f'Quote {response_type} successfully',
            'quote': quote.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

