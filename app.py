from flask import Flask, render_template, request, flash, jsonify, redirect
from formulario import Contactenos

import utils
import os #Agregue la libreria os
import yagmail as yagmail

app = Flask(__name__)

from message import mensajes
from db import get_db

#Ocurrio un eror: The session is unavailable because no secret key was set.
# Set the secret_key on the application to something unique and secret.
app.secret_key = os.urandom(24)
#Esta linea nos va a permitir realizar las peticiones cliente servidor de forma segura por medio de una
#contraseña cifrada, en este caso mande una contraseña que viniera del Sistema operativo de manera aleatoria
#de 24 caracteres

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/home/')
def myHome():
    return render_template('home.html')

@app.route('/login', methods=('GET','POST'))
def login():
    try:
        if request.method == 'POST':
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

            user = db.execute('SELECT * FROM usuarios WHERE usuario=? AND contraseña=?',(username,password)).fetchone()

            if user is None:
               error = 'Usuario o contraseña inválidos'
            else:
                return redirect('mensaje')
            flash(error)
            return render_template('login.html')

        return render_template('login.html')
    except TypeError as e:
        print("Ocurrio un eror:", e)
        return render_template('login.html')

@app.route('/contactenos')
def contactus():
    formulario = Contactenos()
    return render_template('contactenos.html',titulo='Contactenos', form= formulario)

@app.route('/register', methods=('GET','POST'))
def register():
    try:
        if request.method == 'POST':
            username = request.form['usuario']
            password = request.form['password']
            email = request.form['email']
            error = None

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

            db.execute('INSERT INTO usuarios (usuario,correo,contraseña) VALUES (?,?,?)',
                (username, email, password)
            )

            db.commit()
            flash('Revisa tu correo para activar tu cuenta')
            return render_template('login.html')

            #serverEmail = yagmail.SMTP('ejemplomisiontic@gmail.com', 'Maracuya1234')

            #serverEmail.send(to=email, subject='Activa tu cuenta',
            #                 contents='Bienvenido, Su cuenta ha sido creada')
        return render_template('register.html')
    except Exception as e:
        #print("Ocurrio un eror:", e)
        return render_template('register.html')

@app.route('/mensaje')
def Message():
    return jsonify({'usuario':mensajes,'mensaje': "Estos son los mensajes"})

if __name__ == '__main__':
    app.run()