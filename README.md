# ASTRID Security Dashboard

The ASTRID Security Dashboard based on `python3.6` and `Django3.0.1`.

## Main Features:

Current release v2.0 :tada:

- [x] show current service topology
- [x] show/edit/manage security policies (still under definition)
- [x] show real-time and historical data
- [x] show/edit local agents and their configuration
- [x] show/edit/manage list of detection algorithms
- [x] show/edit/manage inspection programs
- [x] receive notifications/alerts from algorithms

## Installation

### Virtual Environment

It is recommended to use a virtual environment to install the requirements. You can create one for example by running the following commands (you should have the python3-dev, python3-pip and python3-venv system packages installed):

```bash
python3 -m venv my-venv
source my-venv/bin/activate
```

or use any other python virtual environment/management, e.g.

- https://virtualenv.pypa.io/en/stable/
- https://www.anaconda.com/distribution/
- https://github.com/pyenv/pyenv

Install via pip:

```
pip install -Ur requirements.txt
```

If you do NOT have `pip`, please refer to the pip project for installation:

https://pypi.org/project/pip/

### Configuration

Most configuration can be modified in `astrid/settings.py`.

For general `Django` settings please refer to the `Django` project:

https://docs.djangoproject.com/en/3.0/topics/settings/

## Run

Modify `astrid/settings.py` with your database settings or use the default `sqlite3`.

### Create the database

You can make the initial `sqlite3` database with the following commands in the terminal:

```bash
python manage.py migrate
```
### Create a super user

```bash
python manage.py createsuperuser
```

### Running the Django server

```bash
python manage.py runserver
```

You should be able to visit the dashboard and administration in your browser:

- http://127.0.0.1:8000/dashboard
- http://127.0.0.1:8000/admin

### Running in production
It is recommended to run the Django application with a WSGI HTTP server behind a reverse proxy, for example `gunicorn` https://gunicorn.org/ and `nginx` https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/ to handle TLS.

For more information on deployment please refer to:

https://docs.djangoproject.com/en/3.0/howto/deployment/