def ijoin(
    iterable,
    separator: str = "",
    start: str = "",
    end: str = "",
    str_strip: bool = False,
    remove_empty: bool = False,
) -> str:
    if str_strip:
        iterable = (str(x).strip() for x in iterable)
    if remove_empty:
        iterable = (x for x in iterable if x)
    body = separator.join(iterable)
    return f"{start}{body}{end}"
