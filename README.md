Runs at https://zifb.in

To get this running, install nginx and pip

Run 'pip install -r requirements.txt'

Basic nginx config: 

    server {
        listen [::]:80;
        server_name  zifb.in;

        location / { try_files $uri @zifbin; }
        location @zifbin {
            include uwsgi_params;
            uwsgi_pass unix:/tmp/uwsgi.sock;
        }
    }

Good luck!
