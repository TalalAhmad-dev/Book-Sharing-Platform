import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    #TODO: Add explict case handling for allowed file sizes and types - In API routes for book uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # Maximum 16 MB