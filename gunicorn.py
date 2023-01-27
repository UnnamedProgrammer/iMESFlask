import multiprocessing




wsgi_app="run:app"
bind='192.168.107.44:5000'
workers=multiprocessing.cpu_count()*2+1

