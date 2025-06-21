from flask import Blueprint, request, jsonify, current_app
from flask_mail import Mail, Message
from src.models.user import db, Quote, User
from src.routes.user import token_required
import json
from datetime import datetime

quote_bp = Blueprint('quote', __name__)

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

@quote_bp.route('/quote', methods=['POST'])
def submit_quote():
    try:
        data = request.get_json()
        
        # Vérifier si l'utilisateur a un compte
        has_account = data.get('withAccount', False)
        user_id = None
        
        if has_account:
            # Récupérer l'utilisateur connecté
            auth_header = request.headers.get('Authorization')
            if auth_header:
                import jwt
                token = auth_header.split(' ')[1]
                try:
                    decoded_token = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                    user_id = decoded_token['user_id']
                except:
                    pass
        
        # Créer une nouvelle demande de devis
        new_quote = Quote(
            project_type=data['projectType'],
            features=json.dumps(data['features']),
            budget=data['budget'],
            timeline=data['timeline'],
            company=data['company'],
            email=data['email'],
            phone=data.get('phone', ''),
            description=data['description'],
            estimated_price=data['estimatedPrice'],
            user_id=user_id,
            has_account=has_account
        )
        
        db.session.add(new_quote)
        db.session.commit()
        
        # Préparer l'email pour l'admin
        email_subject = f"Nouvelle demande de devis - {data['company']}"
        account_info = "Avec compte utilisateur" if has_account else "Sans compte (invité)"
        
        email_body = f"""
Nouvelle demande de devis reçue sur Buildrr.fr

Type de demande: {account_info}

Informations client:
- Nom de l'entreprise: {data['company']}
- Email: {data['email']}
- Téléphone: {data.get('phone', 'Non renseigné')}

Détails du projet:
- Type de projet: {data['projectType']}
- Budget approximatif: {data['budget']}
- Délai souhaité: {data['timeline']}
- Fonctionnalités: {', '.join(data['features'])}

Description:
{data['description']}

Estimation automatique: {data['estimatedPrice']}€

---
Demande reçue le: {new_quote.created_at.strftime('%d/%m/%Y à %H:%M')}
ID de la demande: {new_quote.id}

{"Le client a un compte et pourra suivre sa demande dans son dashboard." if has_account else "Le client n'a pas de compte, répondez par email uniquement."}

Pour répondre à cette demande, connectez-vous au dashboard admin.
        """
        
        # Envoyer l'email à l'admin
        email_sent = send_email(email_subject, 'contact@buildrr.fr', email_body)
        
        return jsonify({
            'message': 'Quote submitted successfully',
            'quoteId': new_quote.id,
            'emailSent': email_sent,
            'hasAccount': has_account
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@quote_bp.route('/quotes', methods=['GET'])
def get_quotes():
    try:
        quotes = Quote.query.order_by(Quote.created_at.desc()).all()
        return jsonify({
            'quotes': [quote.to_dict() for quote in quotes]
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@quote_bp.route('/quotes/user', methods=['GET'])
@token_required
def get_user_quotes(current_user):
    """Récupérer les devis de l'utilisateur connecté"""
    try:
        quotes = Quote.query.filter_by(user_id=current_user.id).order_by(Quote.created_at.desc()).all()
        return jsonify({
            'quotes': [quote.to_dict() for quote in quotes]
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@quote_bp.route('/quotes/<int:quote_id>/respond', methods=['POST'])
@token_required
def user_respond_to_quote(current_user, quote_id):
    """Permettre à l'utilisateur de répondre à un devis"""
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
        
        # Envoyer un email à l'admin
        subject = f"Réponse au devis #{quote.id} - {quote.company}"
        response_text = "ACCEPTÉ" if response_type == 'accepted' else "REFUSÉ"
        
        email_body = f"""
Le client a répondu au devis #{quote.id}

Réponse: {response_text}

Informations client:
- Entreprise: {quote.company}
- Email: {quote.email}
- Téléphone: {quote.phone or 'Non renseigné'}

Projet: {quote.project_type}
Prix proposé: {quote.admin_price}€

Message du client:
{message}

---
Réponse reçue le: {datetime.utcnow().strftime('%d/%m/%Y à %H:%M')}

Connectez-vous au dashboard admin pour plus de détails.
        """
        
        send_email(subject, 'contact@buildrr.fr', email_body)
        
        return jsonify({
            'message': f'Quote {response_type} successfully',
            'quote': quote.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

