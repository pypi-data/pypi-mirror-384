import subprocess

from packaging.version import Version
from tomlkit import dumps, parse


class PyPi:
    email = "ufiapjj@gmail.com"
    password = "dzukhron"

    class Token:
        name = "token"
        scope = "All Projects"
        value = (
            "pypi-AgEIcHlwaS5vcmcCJGI0NzJhYTcwLWVmMjctNDQ0NS1hZjVjLTIyOT"
            "NiZWYyYzc3ZQACKlszLCJkMTdmMWM4OC0xZGVlLTQ5OWQtOWRjNy1mNjhhY"
            "jFkMjlhMDgiXQAABiAHa_VLiA5jhV-9mGcCIPANaWCSgFmZCcc53YK_XWcv3Q"
        )


def update_version(rule="patch"):
    path = "pyproject.toml"
    doc = parse(open(path, encoding="utf-8").read())
    v_old = Version(str(doc["project"]["version"]))
    v_new = {
        "major": f"{v_old.major + 1}.0.0",
        "minor": f"{v_old.major}.{v_old.minor + 1}.0",
        "patch": f"{v_old.major}.{v_old.minor}.{v_old.micro + 1}",
    }[rule]
    doc["project"]["version"] = v_new
    open(path, "w", encoding="utf-8").write(dumps(doc))
    print(str(v_old), " -> ", v_new)
    return str(v_old), v_new


def sub_run(*args):
    for i in args:
        subprocess.run(i, shell=True)


if __name__ == "__main__":
    commit = input("commit for : ")
    sub_run(
        "git pull",
        "git status",
        "git add .",
        f"git commit -m '{commit}'",
        "git push",
    )
    update_version()
    sub_run(
        "flit build",
        "flit publish",
    )
