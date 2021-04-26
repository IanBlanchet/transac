import os
from dotenv import load_dotenv
load_dotenv()


class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu le devinera pas'
	DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///pos.db'
