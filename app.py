from flask import Flask, render_template, request, flash, jsonify, redirect, session, g, url_for, send_file, make_response
from formulario import Contactenos
from message import mensajes
from db import get_db, close_db
from werkzeug.security import generate_password_hash, check_password_hash

import utils
import os  # Agregue la libreria os
import functools

app = Flask(__name__)
# Ocurrio un eror: The session is unavailable because no secret key was set.
# Set the secret_key on the application to something unique and secret.
app.secret_key = os.urandom(24)
# Esta linea nos va a permitir realizar las peticiones cliente servidor de forma segura por medio de una
# contraseña cifrada, en este caso mande una contraseña que viniera del Sistema operativo de manera aleatoria
# de 24 caracteres

@app.route('/')
def hello_world():
    if g.user:
        return redirect(url_for('send'))
    return render_template('login.html')


@app.route('/login', methods=('GET', 'POST'))
def login():
    try:
        if g.user:
            return redirect(url_for('send'))
        if request.method == 'POST':
            close_db()
            db = get_db()
            username = request.form['usuario']
            password = request.form['password']

            if not username:
                error = "Debes ingresar el usuario"
                flash(error)
                return render_template('login.html')
            if not password:
                error = "Contraseña es requerida"
                flash(error)
                return render_template('login.html')

            print("usuario" + username + " clave:" + password)

            user = db.execute(
                'SELECT * FROM usuarios WHERE usuario = ?', (username, )
            ).fetchone()

            print(user[3])
            if user is None:
                error = 'Usuario o contraseña inválidos'
            else:
                if check_password_hash(user[3], password):
                    session.clear()
                    session['user_id'] = user[0]
                    resp = make_response(redirect(url_for('send')))
                    resp.set_cookie('username', username)
                    print(resp)
                    return redirect(url_for('send'))
            flash(error)
            return render_template('login.html')

        return render_template('login.html')
    except TypeError as e:
        print("Ocurrio un eror:", e)
        return render_template('login.html')


@app.route('/hello')
def getcookie():
    name = request.cookies.get('username')
    return '<h1>'+name+'</h1>'

@app.route('/contactenos')
def contactus():
    formulario = Contactenos()
    return render_template('contactenos.html', titulo='Contactenos', form=formulario)


def login_required(view):
    @functools.wraps( view )
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect( url_for( 'login' ) )
        return view( **kwargs )

    return wrapped_view

@app.route('/register', methods=('GET', 'POST'))
def register():
    if g.user:
        return redirect(url_for('send'))
    try:
        if request.method == 'POST':
            username = request.form['usuario']
            password = request.form['password']
            email = request.form['email']
            error = None
            close_db()
            db = get_db()

            if not utils.isUsernameValid(username):
                error = "El usuario debe ser alfanumerico"
                flash(error)
                return render_template('register.html')

            if not utils.isEmailValid(email):
                error = 'Correo inválido'
                flash(error)
                return render_template('register.html')

            if not utils.isPasswordValid(password):
                error = 'La contraseña debe tener por los menos una mayúcscula y una mínuscula y 8 caracteres'
                flash(error)
                return render_template('register.html')

            if db.execute('SELECT id FROM usuarios WHERE correo=?', (email,)).fetchone() is not None:
                error = 'El correo ya existe'.format(email)
                flash(error)
                return render_template('login.html')

            hashPassword = generate_password_hash(password)

            print(hashPassword)

            query = 'INSERT INTO usuarios (usuario,correo,contraseña) VALUES (?,?,?)', (username, email, hashPassword)
            print(query)
            db.execute(
                'INSERT INTO usuarios (usuario, correo, contraseña) VALUES (?,?,?)',
                (username, email, hashPassword)
            )

            db.commit()
            flash('Revisa tu correo para activar tu cuenta')
            return render_template('login.html')
        # serverEmail = yagmail.SMTP('ejemplomisiontic@gmail.com', 'Maracuya1234')
        # serverEmail.send(to=email, subject='Activa tu cuenta',
        #                 contents='Bienvenido, Su cuenta ha sido creada')
        return render_template('register.html')
    except Exception as e:
        print(e)
        return render_template('register.html')


@app.route('/mensaje')
def Message():
    return jsonify({'usuario': mensajes, 'mensaje': "Estos son los mensajes"})


@app.route('/send', methods=('GET', 'POST'))
@login_required
def send():
    if request.method == 'POST':
        from_id = g.user[0]

        name  = g.user[1]
        print(name)
        print(from_id)
        to_username = request.form['para']
        subject = request.form['asunto']
        body = request.form['mensaje']

        name = request.cookies.get('username')
        print(name)
        if not to_username:
            flash(':Para campo requerido');
            return render_template('send.html')

        if not subject:
            flash(':Asunto es requerido');
            return render_template('send.html')

        if not body:
            flash(':Mensaje es requerido');
            return render_template('send.html')

        error = None
        userto = None

        close_db()
        db = get_db()

        if db is not None:
            userto = db.execute(
                'SELECT * FROM usuarios WHERE usuario = ?', (to_username,)
        ).fetchone()
        else:
            return redirect('mensaje')

        if userto is None:
            error = 'No existe el usuario digitado'

        if error is not None:
            flash(error)
        else:
            close_db()
            db = get_db()
            db.execute(
                'INSERT INTO mensajes (from_id, to_id, asunto, mensaje)'
                ' VALUES (?, ?, ?, ?)',
                (g.user[0], userto[0], subject, body)
            )
            db.commit()
            flash("Mensaje Enviado")

    return render_template('send.html')

@app.before_request
def load_logged_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        close_db()
        g.user = get_db().execute(
            'SELECT * FROM usuarios WHERE id=?', (user_id,)

        ).fetchone()


@app.route('/downloadimage', methods=('GET', 'POST'))
# @login_required
def downloadimage():
    return send_file("../review/sesion15/resources/image.png", as_attachment=True)

@app.route( '/downloadpdf', methods=('GET', 'POST') )
@login_required
def downloadpdf():
    return send_file( "../review/sesion15/resources/doc.pdf", as_attachment=True )


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
