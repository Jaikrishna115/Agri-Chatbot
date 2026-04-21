import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from deep_translator import GoogleTranslator
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# Import your existing chatbot and ingestion logic
from chatbot import ask_bot
from ingest import add_file_to_db

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = 'agri-secret-key-999'  # Change this for production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agri_advisor.db'
app.config['UPLOAD_FOLDER'] = 'data'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure data folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- DATABASE SETUP ---
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home' # Redirect to home if not logged in

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_msg = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create Database
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- HELPER FUNCTIONS ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def translate_text(text, target_lang):
    if target_lang == 'en': return text
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except:
        return text

# --- ROUTES ---

@app.route("/")
def home():
    return render_template("index.html")

# --- AUTH ROUTES (NEW) ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400
    
    # Corrected: Removed method='sha256'
    hashed_pw = generate_password_hash(password)
    
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully! Please login.'}), 201

# --- MAKE SURE THIS IS ON A NEW LINE AND NOT INDENTED ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({'message': 'Login Successful', 'username': user.username})
    
    return jsonify({'message': 'Invalid Username or Password'}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/check_session', methods=['GET'])
def check_session():
    if current_user.is_authenticated:
        return jsonify({'logged_in': True, 'username': current_user.username})
    return jsonify({'logged_in': False})

# --- DOCUMENT ROUTES ---
@app.route("/upload_document", methods=["POST"])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            success = add_file_to_db(filepath) 
            if success:
                return jsonify({"success": f"Learned from {filename} successfully!"})
            else:
                return jsonify({"error": "Failed to process file."}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"error": "Invalid file type. Only PDF allowed."}), 400

# --- CHAT ROUTE (UPDATED) ---
@app.route("/get_response", methods=["POST"])
@login_required  # <--- Ensures only logged-in users can chat
def get_response():
    user_message = request.form["msg"]
    selected_lang = request.form.get("lang", "en")

    lang_map = {"hi": "Hindi", "te": "Telugu", "ta": "Tamil", "kn": "Kannada", "en": "English"}
    target_language_name = lang_map.get(selected_lang, "English")

    # 1. Translate & Prepare Query
    english_query = translate_text(user_message, "en") if selected_lang != "en" else user_message
    
    if selected_lang != "en":
        final_query = f"{english_query} (IMPORTANT: Answer this question in {target_language_name} language only, but keep formatting like bold and lists)"
    else:
        final_query = english_query

    # 2. Get Answer from Bot
    bot_response, sources = ask_bot(final_query)

    # 3. Save to Database (LINKED TO CURRENT USER)
    new_chat = ChatHistory(
        user_id=current_user.id, 
        user_msg=user_message, 
        bot_response=bot_response
    )
    db.session.add(new_chat)
    db.session.commit()
    
    # 4. Handle Sources
    source_files = list(set([os.path.basename(s) for s in sources])) if sources else []

    return jsonify({
        "response": bot_response, 
        "sources": source_files 
    })

# --- HISTORY ROUTE (UPDATED) ---
@app.route("/history", methods=["GET"])
@login_required # <--- Ensures users only see THEIR OWN history
def get_history():
    # Fetch history ONLY for the current user
    history = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp).all()
    
    data = [{"user_msg": h.user_msg, "bot_response": h.bot_response} for h in history]
    return jsonify(data)

@app.route("/delete_history", methods=["POST"])
@login_required
def delete_history():
    # Delete only current user's history
    ChatHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"success": True})

@app.route("/get_stats", methods=["GET"])
def get_stats():
    try:
        file_count = len([f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.pdf')])
        return jsonify({"file_count": file_count, "status": "Online"})
    except Exception as e:
        return jsonify({"file_count": 0, "status": "Offline"})

# --- ACCOUNT MANAGEMENT ROUTES ---

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    old_pass = data.get('old_password')
    new_pass = data.get('new_password')

    # 1. Verify Old Password
    if not check_password_hash(current_user.password, old_pass):
        return jsonify({'success': False, 'message': 'Incorrect old password'})

    # 2. Update to New Password (using default secure hash)
    current_user.password = generate_password_hash(new_pass)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password updated successfully!'})

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    try:
        # 1. Delete User's Chat History first
        ChatHistory.query.filter_by(user_id=current_user.id).delete()
        
        # 2. Delete the User
        user_to_delete = User.query.get(current_user.id)
        db.session.delete(user_to_delete)
        db.session.commit()
        
        # 3. Logout
        logout_user()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == "__main__":
    print("🚀 Starting Agri-Advisor Server with Login System...")
    app.run(debug=True, use_reloader=False, threaded=True, port=5001)