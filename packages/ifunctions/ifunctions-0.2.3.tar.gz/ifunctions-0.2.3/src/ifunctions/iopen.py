IOPEN_BUFFER = 65536
IOPEN_ENCODE = "utf-8"


def iopen(path, data=None, append=False):
    if data is None:
        with open(path, "r", encoding=IOPEN_ENCODE, buffering=IOPEN_BUFFER) as f:
            return f.read()

    m = "w" if not append else "a"
    with open(path, m, encoding=IOPEN_ENCODE, buffering=IOPEN_BUFFER) as f:
        return f.write(data)
