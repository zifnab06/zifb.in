sudo -u www-data uwsgi -s /tmp/uwsgi.sock --module app --callable app > /var/log/zifb.in.log 2> /var/log/zifb.in.log &
