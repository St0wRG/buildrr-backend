from flask import Blueprint, request, jsonify, current_app
from flask_mail import Mail, Message
from src.models.user import db, Contact

contact_bp = Blueprint('contact', __name__)

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

@contact_bp.route('/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.get_json()
        
        # Créer un nouveau message de contact
        new_contact = Contact(
            name=data['name'],
            email=data['email'],
            company=data.get('company', ''),
            phone=data.get('phone', ''),
            subject=data['subject'],
            message=data['message']
        )
        
        db.session.add(new_contact)
        db.session.commit()
        
        # Préparer l'email
        email_subject = f"Nouveau message de contact - {data['subject']}"
        email_body = f"""
Nouveau message de contact reçu sur Buildrr.fr

Informations de contact:
- Nom: {data['name']}
- Email: {data['email']}
- Entreprise: {data.get('company', 'Non renseigné')}
- Téléphone: {data.get('phone', 'Non renseigné')}
- Sujet: {data['subject']}

Message:
{data['message']}

---
Message reçu le: {new_contact.created_at.strftime('%d/%m/%Y à %H:%M')}
ID du message: {new_contact.id}

Pour répondre à ce message, connectez-vous au dashboard admin.
        """
        
        # Envoyer l'email
        email_sent = send_email(email_subject, 'contact@buildrr.fr', email_body)
        
        return jsonify({
            'message': 'Contact message submitted successfully',
            'contactId': new_contact.id,
            'emailSent': email_sent
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@contact_bp.route('/contacts', methods=['GET'])
def get_contacts():
    try:
        contacts = Contact.query.order_by(Contact.created_at.desc()).all()
        return jsonify({
            'contacts': [contact.to_dict() for contact in contacts]
        }), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

