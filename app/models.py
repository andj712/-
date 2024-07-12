from flask_sqlalchemy import SQLAlchemy 

db = SQLAlchemy()

class UserFavs(db.Model):
	username = db.Column(db.String, primary_key=True)
	mesto = db.Column(db.String)
	hrana = db.Column(db.String)

	def __init__(self, username, mesto, hrana):
		self.username=username
		self.mesto=mesto
		self.hrana=hrana

	def __repr__(self):
		return f'<User-Mesto-Hrana : {self.username}-{self.mesto}-{self.hrana}'

