from flask import Blueprint, request, jsonify
from src.models.user import db, User, Order, Quote, Contact, PrivateMessage, SiteContent
from src.routes.user import token_required
from werkzeug.security import generate_password_hash
from flask_mail import Mail, Message
from flask import current_app
import json
import csv
import io
from datetime import datetime
import random
import string

admin_bp = Blueprint('admin', __name__)

def send_email(subject, recipient, body):
    """Fonction utilitaire pour envoyer des emails"""
    try:
        mail = Mail(current_app)
        msg = Message(
            subject=subject,
            recipients=[recipient],
            body=body,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erreur envoi email: {str(e)}")
        return False

from functools import wraps

def admin_required(f):
    """Décorateur pour vérifier les permissions admin"""
    @wraps(f)
    def admin_decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return admin_decorated

# ===== GESTION DES UTILISATEURS =====

@admin_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_user(current_user, user_id):
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if 'firstName' in data:
            user.first_name = data['firstName']
        if 'lastName' in data:
            user.last_name = data['lastName']
        if 'email' in data:
            user.email = data['email']
        if 'company' in data:
            user.company = data['company']
        if 'phone' in data:
            user.phone = data['phone']
        if 'role' in data:
            user.role = data['role']
        if 'isActive' in data:
            user.is_active = data['isActive']
        if 'password' in data:
            user.password = generate_password_hash(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    try:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            return jsonify({'message': 'Cannot delete your own account'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/users', methods=['POST'])
@token_required
@admin_required
def create_user(current_user):
    try:
        data = request.get_json()
        
        # Vérifier si l'email existe déjà
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        new_user = User(
            first_name=data['firstName'],
            last_name=data['lastName'],
            email=data['email'],
            password=generate_password_hash(data['password']),
            company=data.get('company', ''),
            phone=data.get('phone', ''),
            role=data.get('role', 'member')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': new_user.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ===== GESTION DES COMMANDES =====

@admin_bp.route('/orders', methods=['GET'])
@token_required
@admin_required
def get_all_orders(current_user):
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/orders', methods=['POST'])
@token_required
@admin_required
def create_order(current_user):
    try:
        data = request.get_json()
        
        new_order = Order(
            order_id=''.join(random.choices(string.ascii_uppercase + string.digits, k=8)),
            title=data['title'],
            type=data['type'],
            status=data.get('status', 'pending'),
            price=data['price'],
            description=data.get('description', ''),
            progress=data.get('progress', 0),
            user_id=data['userId']
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        return jsonify({
            'message': 'Order created successfully',
            'order': new_order.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/orders/<int:order_id>', methods=['PUT'])
@token_required
@admin_required
def update_order(current_user, order_id):
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        
        if 'title' in data:
            order.title = data['title']
        if 'type' in data:
            order.type = data['type']
        if 'status' in data:
            order.status = data['status']
            if data['status'] == 'completed':
                order.completed_at = datetime.utcnow()
        if 'price' in data:
            order.price = data['price']
        if 'description' in data:
            order.description = data['description']
        if 'progress' in data:
            order.progress = data['progress']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Order updated successfully',
            'order': order.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_order(current_user, order_id):
    try:
        order = Order.query.get_or_404(order_id)
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'message': 'Order deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ===== GESTION DES DEVIS =====

@admin_bp.route('/quotes', methods=['GET'])
@token_required
@admin_required
def get_all_quotes(current_user):
    try:
        quotes = Quote.query.order_by(Quote.created_at.desc()).all()
        return jsonify({
            'quotes': [quote.to_dict() for quote in quotes]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/quotes/<int:quote_id>', methods=['PUT'])
@token_required
@admin_required
def update_quote(current_user, quote_id):
    try:
        quote = Quote.query.get_or_404(quote_id)
        data = request.get_json()
        
        if 'status' in data:
            quote.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Quote updated successfully',
            'quote': quote.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/quotes/<int:quote_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_quote(current_user, quote_id):
    try:
        quote = Quote.query.get_or_404(quote_id)
        db.session.delete(quote)
        db.session.commit()
        
        return jsonify({'message': 'Quote deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ===== GESTION DES CONTACTS =====

@admin_bp.route('/contacts', methods=['GET'])
@token_required
@admin_required
def get_all_contacts(current_user):
    try:
        contacts = Contact.query.order_by(Contact.created_at.desc()).all()
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/contacts/<int:contact_id>', methods=['PUT'])
@token_required
@admin_required
def update_contact(current_user, contact_id):
    try:
        contact = Contact.query.get_or_404(contact_id)
        data = request.get_json()
        
        if 'status' in data:
            contact.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Contact updated successfully',
            'contact': contact.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_contact(current_user, contact_id):
    try:
        contact = Contact.query.get_or_404(contact_id)
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({'message': 'Contact deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ===== GESTION DES MESSAGES PRIVÉS =====

@admin_bp.route('/messages', methods=['GET'])
@token_required
@admin_required
def get_all_messages(current_user):
    try:
        messages = PrivateMessage.query.order_by(PrivateMessage.created_at.desc()).all()
        return jsonify({
            'messages': [message.to_dict() for message in messages]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/messages/<int:message_id>/read', methods=['PUT'])
@token_required
@admin_required
def mark_message_read(current_user, message_id):
    try:
        message = PrivateMessage.query.get_or_404(message_id)
        message.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Message marked as read'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/messages', methods=['POST'])
@token_required
@admin_required
def send_admin_message(current_user):
    try:
        data = request.get_json()
        
        new_message = PrivateMessage(
            subject=data['subject'],
            message=data['message'],
            sender_id=current_user.id,
            recipient_id=data['recipientId']
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({
            'message': 'Message sent successfully',
            'messageId': new_message.id
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ===== GESTION DU CONTENU DU SITE =====

@admin_bp.route('/content', methods=['GET'])
@token_required
@admin_required
def get_site_content(current_user):
    try:
        content = SiteContent.query.all()
        return jsonify({
            'content': [item.to_dict() for item in content]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/content', methods=['POST'])
@token_required
@admin_required
def create_content(current_user):
    try:
        data = request.get_json()
        
        new_content = SiteContent(
            page_name=data['pageName'],
            section_name=data['sectionName'],
            content_type=data['contentType'],
            content=data['content'],
            is_active=data.get('isActive', True)
        )
        
        db.session.add(new_content)
        db.session.commit()
        
        return jsonify({
            'message': 'Content created successfully',
            'content': new_content.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/content/<int:content_id>', methods=['PUT'])
@token_required
@admin_required
def update_content(current_user, content_id):
    try:
        content = SiteContent.query.get_or_404(content_id)
        data = request.get_json()
        
        if 'pageName' in data:
            content.page_name = data['pageName']
        if 'sectionName' in data:
            content.section_name = data['sectionName']
        if 'contentType' in data:
            content.content_type = data['contentType']
        if 'content' in data:
            content.content = data['content']
        if 'isActive' in data:
            content.is_active = data['isActive']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Content updated successfully',
            'content': content.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/content/<int:content_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_content(current_user, content_id):
    try:
        content = SiteContent.query.get_or_404(content_id)
        db.session.delete(content)
        db.session.commit()
        
        return jsonify({'message': 'Content deleted successfully'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ===== STATISTIQUES ADMIN =====

@admin_bp.route('/stats', methods=['GET'])
@token_required
@admin_required
def get_admin_stats(current_user):
    try:
        # Statistiques générales
        total_users = User.query.count()
        total_orders = Order.query.count()
        total_quotes = Quote.query.count()
        total_contacts = Contact.query.count()
        unread_messages = PrivateMessage.query.filter_by(recipient_id=current_user.id, is_read=False).count()
        
        # Revenus
        total_revenue = db.session.query(db.func.sum(Order.price)).filter_by(status='completed').scalar() or 0
        pending_revenue = db.session.query(db.func.sum(Order.price)).filter_by(status='pending').scalar() or 0
        
        # Commandes par statut
        orders_by_status = {
            'pending': Order.query.filter_by(status='pending').count(),
            'in_progress': Order.query.filter_by(status='in-progress').count(),
            'completed': Order.query.filter_by(status='completed').count(),
            'cancelled': Order.query.filter_by(status='cancelled').count()
        }
        
        # Devis par statut
        quotes_by_status = {
            'pending': Quote.query.filter_by(status='pending').count(),
            'reviewed': Quote.query.filter_by(status='reviewed').count(),
            'converted': Quote.query.filter_by(status='converted').count(),
            'rejected': Quote.query.filter_by(status='rejected').count()
        }
        
        return jsonify({
            'stats': {
                'totalUsers': total_users,
                'totalOrders': total_orders,
                'totalQuotes': total_quotes,
                'totalContacts': total_contacts,
                'unreadMessages': unread_messages,
                'totalRevenue': total_revenue,
                'pendingRevenue': pending_revenue,
                'ordersByStatus': orders_by_status,
                'quotesByStatus': quotes_by_status
            }
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ===== EXPORT/IMPORT DE DONNÉES =====

@admin_bp.route('/export/<string:data_type>', methods=['GET'])
@token_required
@admin_required
def export_data(current_user, data_type):
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        if data_type == 'users':
            users = User.query.all()
            writer.writerow(['ID', 'Prénom', 'Nom', 'Email', 'Entreprise', 'Téléphone', 'Rôle', 'Actif', 'Date création'])
            for user in users:
                writer.writerow([
                    user.id, user.first_name, user.last_name, user.email,
                    user.company, user.phone, user.role, user.is_active,
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ''
                ])
        
        elif data_type == 'orders':
            orders = Order.query.all()
            writer.writerow(['ID', 'Titre', 'Type', 'Statut', 'Prix', 'Progression', 'Utilisateur', 'Date création'])
            for order in orders:
                writer.writerow([
                    order.order_id, order.title, order.type, order.status,
                    order.price, order.progress, order.user_id,
                    order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else ''
                ])
        
        elif data_type == 'quotes':
            quotes = Quote.query.all()
            writer.writerow(['ID', 'Type projet', 'Entreprise', 'Email', 'Prix estimé', 'Statut', 'Date création'])
            for quote in quotes:
                writer.writerow([
                    quote.id, quote.project_type, quote.company, quote.email,
                    quote.estimated_price, quote.status,
                    quote.created_at.strftime('%Y-%m-%d %H:%M:%S') if quote.created_at else ''
                ])
        
        elif data_type == 'contacts':
            contacts = Contact.query.all()
            writer.writerow(['ID', 'Nom', 'Email', 'Entreprise', 'Sujet', 'Statut', 'Date création'])
            for contact in contacts:
                writer.writerow([
                    contact.id, contact.name, contact.email, contact.company,
                    contact.subject, contact.status,
                    contact.created_at.strftime('%Y-%m-%d %H:%M:%S') if contact.created_at else ''
                ])
        
        else:
            return jsonify({'message': 'Invalid data type'}), 400
        
        output.seek(0)
        return jsonify({
            'data': output.getvalue(),
            'filename': f'{data_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500



# ===== GESTION DES RÉPONSES AUX DEVIS =====

@admin_bp.route('/quotes/<int:quote_id>/respond', methods=['POST'])
@token_required
@admin_required
def admin_respond_to_quote(current_user, quote_id):
    try:
        quote = Quote.query.get_or_404(quote_id)
        data = request.get_json()
        
        quote.admin_response = data['response']
        quote.admin_price = data['price']
        quote.admin_timeline = data['timeline']
        quote.responded_at = datetime.utcnow()
        quote.status = 'sent'
        
        db.session.commit()
        
        # Envoyer email selon le type de compte
        if quote.has_account:
            # Email pour utilisateur avec compte
            subject = f"Réponse à votre demande de devis - {quote.company}"
            email_body = f"""
Bonjour,

Nous avons étudié votre demande de devis pour votre projet "{quote.project_type}".

Notre proposition:
- Prix: {quote.admin_price}€
- Délai: {quote.admin_timeline}

Message personnalisé:
{quote.admin_response}

Vous pouvez consulter les détails complets et répondre à cette proposition directement dans votre dashboard sur notre site web.

Connectez-vous sur: https://leqdupvb.manus.space/dashboard

Cordialement,
L'équipe Buildrr
            """
        else:
            # Email pour invité
            subject = f"Votre devis personnalisé - {quote.company}"
            email_body = f"""
Bonjour,

Merci pour votre demande de devis pour votre projet "{quote.project_type}".

Voici notre proposition détaillée:

Prix: {quote.admin_price}€
Délai de réalisation: {quote.admin_timeline}

Détails de notre proposition:
{quote.admin_response}

Pour accepter cette proposition ou discuter des détails, vous pouvez nous répondre directement par email ou nous contacter au téléphone.

Nous restons à votre disposition pour toute question.

Cordialement,
Alex Truchy
Buildrr - Build Smart
Email: contact@buildrr.fr
            """
        
        # Envoyer l'email au client
        send_email(subject, quote.email, email_body)
        
        return jsonify({
            'message': 'Response sent successfully',
            'quote': quote.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

