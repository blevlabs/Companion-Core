from cosmo_app import app as application

# Path: wsgi.py

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5077)