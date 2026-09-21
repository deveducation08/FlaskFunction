# importação biblioteca flask

import os
from dotenv import load_dotenv
import requests
from flask import Flask, render_template, session, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_KEY'] = os.environ.get('API_KEY')
app.config['API_URL'] = os.environ.get('API_URL')
app.config['API_FROM'] = os.environ.get('API_FROM')

app.config['FLASKY_MAIL_SUBJECT_PREFIX'] = '[Flasky]'
app.config['FLASKY_ADMIN'] = os.environ.get('FLASKY_ADMIN')

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


def send_simple_message(username):
  	return requests.post(
  		app.config['API_URL'],
  		auth=("api", app.config['API_KEY']),
  		data={"from": app.config['API_FROM'],
			"to": "Norton Rodrigues Lima <norton.rodrigues@aluno.ifsp.edu.br>, Fábio Teixeira <flaskaulasweb@zohomail.com>",
  			"subject": "Hello Norton Rodrigues Lima",
  			"text": f"""Nome: Norton Rodrigues Lima Prontuário: PT3038017 Usuário cadastrado: {username}"""})

# classes revertidas em tabelas

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>' % self.username


# campos formulários definidos por classes

class NameForm(FlaskForm):
    name = StringField('Qual é o seu nome?', validators=[DataRequired()])
    role = SelectField('Qual é a sua função?', coerce=int)
    submit = SubmitField('Enviar')


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# função principal

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    form.role.choices = [(r.id, r.name) for r in Role.query.order_by(Role.name).all()]

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            role_escolhida = Role.query.get(form.role.data)
            user = User(username=form.name.data, role=role_escolhida)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
            send_simple_message(username=form.name.data)
        else:
            session['known'] = True
        session['name'] = form.name.data
        return redirect(url_for('index'))

    if request.method == 'GET':
        role_padrao = Role.query.filter_by(name='User').first()
        if role_padrao:
            form.role.data = role_padrao.id

    pessoas = User.query.all()
    roles = Role.query.order_by(Role.name).all()
    return render_template('index.html', form=form, pessoas=pessoas, roles=roles,
                           name=session.get('name'),
                           known=session.get('known', False))