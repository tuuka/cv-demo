from app import application

if __name__ == '__main__':
    port = application.config.get('PORT', 5000)
    debug = application.config.get('DEBUG', False)
    application.run(host='0.0.0.0', port=port, debug=debug)
