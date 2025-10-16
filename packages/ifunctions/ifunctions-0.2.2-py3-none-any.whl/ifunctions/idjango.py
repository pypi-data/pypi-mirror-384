import subprocess


def django_collectstatic():
    subprocess.run("python manage.py collectstatic --no-input", shell=True)


def django_makemigrations():
    subprocess.run("python manage.py makemigrations", shell=True)


def django_migrate():
    subprocess.run("python manage.py migrate", shell=True)


def django_runserver():
    subprocess.run("python manage.py runserver 0.0.0.0:8080", shell=True)
