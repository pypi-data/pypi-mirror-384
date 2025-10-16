def _icontains(keywords, text):
    it = iter(text.lower())
    _all = all(ch in it for ch in keywords.lower())
    return text if _all else None


def icontains(keywords, text):
    if isinstance(text, str):
        return _icontains(keywords, text)
    if isinstance(text, list):
        return [t for t in text if _icontains(keywords, t)]
