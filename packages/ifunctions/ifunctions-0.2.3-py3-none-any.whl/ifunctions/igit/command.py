import subprocess


def git_status():
    subprocess.run("git status", shell=True)


def git_add():
    subprocess.run("git add .", shell=True)


def git_commit(commit=None):
    if commit is None: 
        commit = input("commit : ")
    subprocess.run(f"git commit -m '{commit}'", shell=True)


def git_push():
    subprocess.run("git push", shell=True)


def git_pull():
    subprocess.run("git pull", shell=True)


def github_pull():
    git_pull()


def github_push(commit):
    git_status()
    git_add()
    git_commit(commit)
    git_push()
