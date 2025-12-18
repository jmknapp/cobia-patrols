bind = "127.0.0.1:5012"
workers = 4  # Plenty for a low-traffic site; was cpu_count * 2 + 1 = 65!
worker_class = "sync"
timeout = 120
keepalive = 5
graceful_timeout = 30  # Give workers time during reload/shutdown
preload_app = True     # Load app before forking workers for faster restarts
errorlog = "/var/log/cobiapatrols/gunicorn_error.log"
accesslog = "/var/log/cobiapatrols/gunicorn_access.log"
loglevel = "info"

