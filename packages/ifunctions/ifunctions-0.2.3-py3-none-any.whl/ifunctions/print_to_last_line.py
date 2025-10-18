def print_to_last_line(text: str, latest=1, clear=True):
    """
    Melakukan print ke konsol tetapi akan menimpa baris terakhir.
    Berguna untuk memberikan progress secara interaktif.

    ```python
    for i in range(5):
        print(str(i) * 10)
    print_to_last_line(f" === last ===")
    ```
    """
    _l = f"\033[{latest}A" if latest else ""
    _c = "\033[K" if clear else ""
    print(f"{_l}{_c}{text}")
