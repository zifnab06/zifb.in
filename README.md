Runs at https://zifb.in

To get this running, install nginx, pip, gunicorn, and supervisor

Run 'pip install -r requirements.txt'


Basic nginx config: 

    upstream zifbin {
        server unix:/tmp/zifbin.sock;
    }

    server {
        listen [::]:80 default_server;
        server_name  zifb.in;

        location / {
            try_files $uri @proxy_to_app;
        }
    
        location /static {
            alias /srv/zifb.in/static/;
        }
        location @proxy_to_app {
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            proxy_pass http://zifbin;
        }
    }


Symlink supervisor.conf to /etc/supervisor/conf.d/zifbin.conf, and run:
    
    supervisorctl reread
    supervisorctl reload zifbin
    supervisor start zifbin


Good luck!
