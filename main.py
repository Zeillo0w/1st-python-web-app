from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from flask import session
from functools import wraps




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'zçeufhezoifjezfàçzefzàeojfzfzepfjafaà=)fajf$afofj'

UPLOAD_FOLDER = 'static/uploads'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class Produit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String(150), nullable=True)


@app.route('/SuperAdminPage')
def index():
    produits = Produit.query.all()
    return render_template('index.html', produits=produits)

@app.route('/AdminPage')
def admin():
    produits = Produit.query.all()
    return render_template('admin.html', produits=produits)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nom = request.form['nom']
        role = "user"
        if nom == "Mathieu":
            role = "superadmin"
        if nom == "Yanis":
            role = "admin"
        session['nom'] = nom
        session['role'] = role
        
        if role == "superadmin":
            return redirect(url_for('index'))
        elif role == "admin":
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('acheter'))
            
    return render_template('login.html')



def role_requis(*roles_requis):  
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            # vérifier si le rôle de l'utilisateur est dans les rôles autorisés
            if get_role_utilisateur() not in roles_requis:
                return "Accès refusé", 403
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


def get_role_utilisateur():
    return session.get('role', 'user')

@app.route('/ajouter', methods=['POST'])
@role_requis('superadmin') 
def ajouter():
    nom = request.form['nom']
    quantite = request.form['quantite']
    image = request.files['image']

    if image and allowed_file(image.filename):
        
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        filename = secure_filename(image.filename)
        image_path = os.path.join('uploads', filename)  
        image_path = image_path.replace('\\', '/')  
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  
        nouveau_produit = Produit(nom=nom, quantite=quantite, image_path=image_path)
   

    else:
        nouveau_produit = Produit(nom=nom, quantite=quantite)

    db.session.add(nouveau_produit)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/modifier/<int:id>', methods=['GET', 'POST'])
@role_requis('admin', 'superadmin')  
def modifier(id):
    produit = Produit.query.get_or_404(id)
    if request.method == 'POST':
        produit.nom = request.form['nom']
        produit.quantite = request.form['quantite']
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join('uploads', filename)
            image_path = image_path.replace('\\', '/')
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            produit.image_path = image_path
        db.session.commit()
        return redirect(url_for('acheter'))
    return render_template('modifier.html', produit=produit)


@app.route('/supprimer/<int:id>', methods=['POST'])
@role_requis('superadmin') 
def supprimer(id):
    produit = Produit.query.get_or_404(id)
    db.session.delete(produit)
    db.session.commit()
    return redirect(url_for('index'))




@app.route('/acheter', methods=['GET'])
def page_acheter():
    produits = Produit.query.all()
    return render_template('acheter.html', produits=produits)


@app.route('/acheter', methods=['POST'])
def acheter():
    panier = session.get('panier', {})
    for id_produit, quantite in panier.items():
        produit = Produit.query.get(id_produit)
        if produit and 0 < quantite <= produit.quantite:
            produit.quantite -= quantite
            db.session.commit()
    # vider le panier après l'achat
    session['panier'] = {}
    return redirect(url_for('acheter'))

@app.route('/ajouter_au_panier', methods=['POST'])
def ajouter_au_panier():
    produit_id = request.form.get('produit_id')
    quantite = int(request.form.get('quantite'))  
    panier = session.get('panier', {})
    panier[str(produit_id)] = panier.get(str(produit_id), 0) + quantite
    session['panier'] = panier
    return redirect(url_for('acheter'))

@app.route('/panier')
def panier():
    panier = session.get('panier', {})
    produits = [(Produit.query.get(id_produit), quantite) for id_produit, quantite in panier.items()]
    return render_template('panier.html', produits=produits)

@app.route('/acceder_au_panier', methods=['POST'])
def acceder_au_panier():
    return redirect(url_for('panier'))

#faire en sorte que le bouton "Accéder au panier" du acheter.html redirige vers la page panier.html
@app.route('/acceder_au_panier', methods=['GET'])
def acceder_au_panier_get():
    return redirect(url_for('panier'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
