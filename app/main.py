from flask import Flask, request, render_template
import redis

app = Flask(__name__)

import os

REDIS_HOST = os.environ['REDIS_HOST']
REDIS_PORT = os.environ['REDIS_PORT']

POSTGRES_HOST = os.environ['POSTGRES_HOST']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PORT = os.environ['POSTGRES_PORT']
POSTGRES_DB = os.environ['POSTGRES_DB']
POSTGRES_PASSWORD = os.environ['PGPASSWORD']

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

# postgresql://username:password@host:port/database
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev'

from models import db, UserFavs

db.init_app(app)
with app.app_context():
    # To create / use database mentioned in URI
    db.create_all()
    db.session.commit()

red = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/save", methods=['POST'])
def save():
    username = str(request.form['username']).lower()
    mesto = str(request.form['mesto']).lower()
    hrana = str(request.form['hrana']).lower()

    # check if data of the username already exists in the redis
    if red.hgetall(username).keys():
        print("hget username:", red.hgetall(username))
        # return a msg to the template, saying the user already exists(from redis)
        return render_template('index.html', user_exists=1, msg='(Iz Redisa)', username=username, mesto=red.hget(username,"mesto").decode('utf-8'), hrana=red.hget(username,"hrana").decode('utf-8'))

    # if not in redis, then check in db
    elif len(list(red.hgetall(username)))==0:
        record =  UserFavs.query.filter_by(username=username).first()
        print("Zapisi preuzeti iz baze", record)
        
        if record:
            red.hset(username, "mesto", mesto)
            red.hset(username, "hrana", hrana)
            # return a msg to the template, saying the user already exists(from database)
            return render_template('index.html', user_exists=1, msg='(Iz baze)', username=username, mesto=record.mesto, hrana=record.hrana)

    # if data of the username doesnot exist anywhere, create a new record in DataBase and store in Redis also
    # create a new record in DataBase
    new_record = UserFavs(username=username, mesto=mesto, hrana=hrana)
    db.session.add(new_record)
    db.session.commit()

    # store in Redis also
    red.hset(username, "mesto", mesto)
    red.hset(username, "hrana", hrana)

    # cross-checking if the record insertion was successful into database
    record =  UserFavs.query.filter_by(username=username).first()
    print("Zapisi preuzeti iz baze nakon inserta", record)

    # cross-checking if the insertion was successful into redis
    print("key-values iz redisa nakon insert:", red.hgetall(username))

    # return a success message upon saving
    return render_template('index.html', saved=1, username=username, mesto=red.hget(username, "mesto").decode('utf-8'), hrana=red.hget(username, "hrana").decode('utf-8'))

@app.route("/keys", methods=['GET'])
def keys():
	records = UserFavs.query.all()
	names = []
	for record in records:
		names.append(record.username)
	return render_template('index.html', keys=1, usernames=names)


@app.route("/get", methods=['POST'])
def get():
	username = request.form['username']
	print("Username:", username)
	user_data = red.hgetall(username)
	print("GET Redis:", user_data)

	if not user_data:
		record = UserFavs.query.filter_by(username=username).first()
		print("Vrati zapis:", record)
		if not record:
			print("Nema podataka u bazi i redisu")
			return render_template('index.html', no_record=1, msg=f"Nije jos definisan zapis za {username}")
		red.hset(username, "mesto", record.mesto)
		red.hset(username, "hrana", record.hrana)
		return render_template('index.html', get=1, msg="(Iz Baze)",username=username, mesto=record.mesto, hrana=record.hrana)
	return render_template('index.html',get=1, msg="(Iz Redisa)", username=username, mesto=user_data[b'mesto'].decode('utf-8'), hrana=user_data[b'hrana'].decode('utf-8'))