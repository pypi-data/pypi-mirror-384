# Mise en production (Debian)

Une possibilité parmi d'autres est d'utiliser un serveur WSGI monté derrière un serveur web en reverse proxy. 
Pour la partie web, exemple avec Apache :

    a2enmod proxy_http

En production, lorsque le debug est désactivé, l'application ne prend pas en charge le service des assets, on doit
donc collecter toutes les ressources statiques dans un dossier :

    ./manage.py collectstatic
    
Puis dans la configuration de votre vhost:

    <Directory /path/to/jama/static>
        Require all granted
    </Directory>
    ProxyPass /static !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

Toujours dans le virtualenv, installez gunicorn:

    pip install gunicorn
    
Gunicorn est un serveur d'applications pour Python. Il maintient un pool de workers.
    
Crééz ensuite un nouveau service pour systemd dans /etc/systemd/system/jama.service:

    [Unit]
    Description=Jama Service
    
    [Service]
    Type=simple
    User=YourAppUser
    Group=YourAppGroup
    UMask=007
    ExecStart=/path/to/your/venv/bin/gunicorn --error-logfile /path/to/error.log --timeout 120 -b 127.0.0.1:8000 -w 5 --pythonpath /path/to/jama jama.wsgi
    Environment="PATH=/usr/bin/:/path/to/your/venv/bin:$PATH"
    Environment="JAMA_SECRET=AddY0uRoWns3crEth3re"
    Environment="JAMA_DEBUG=0"
    Environment="JAMA_SITE=http://localhost:8000/"
    Environment="JAMA_DB_HOST=localhost"
    Environment="JAMA_DB_PORT=5432"
    Environment="JAMA_DB_NAME=dbname"
    Environment="JAMA_DB_USER=dbuser"
    Environment="JAMA_DB_PASSWORD=dbpassword"
    Environment="JAMA_IIIF_DIR=/path/to/iiif_dir"
    Environment="JAMA_FILES_DIR=/path/to/medias/sources"
    Environment="JAMA_IIIF_ENDPOINT=https://www.domain.tld/fcgi-bin/iipsrv.fcgi?IIIF="
    Restart=always
    RestartSec=5
    TimeoutStopSec=10
    
    [Install]
    WantedBy=multi-user.target
    
Puis mettez à jour systemd...

    systemctl daemon-reload
    
...avant de démarrer Jama :

    systemctl start jama
