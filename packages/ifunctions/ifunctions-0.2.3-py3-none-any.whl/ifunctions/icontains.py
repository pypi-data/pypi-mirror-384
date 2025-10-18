def _icontains(keywords: str, text: str) -> bool:
    """
    Mengecek apakah semua karakter dari 'keywords' muncul secara berurutan 
    (namun tidak harus bersebelahan) di dalam 'text', tanpa memperhatikan huruf besar-kecil.
    
    Contoh:
    --------
    >>> _icontains("abc", "a_b_C_d")
    True  # karena 'a' lalu 'b' lalu 'c' muncul dalam urutan itu di dalam text

    >>> _icontains("abc", "acb")
    False  # urutannya berbeda

    """
    it = iter(text.lower())  # buat iterator dari text huruf kecil
    return all(ch in it for ch in keywords.lower())  # cek setiap huruf keywords


def icontains(keywords: str, texts):
    """
    Mencari teks yang mengandung karakter-karakter 'keywords' 
    secara berurutan (tanpa peduli kapitalisasi huruf).

    Dapat digunakan untuk satu string atau daftar string (list of str).

    Contoh:
    --------
    >>> icontains("abc", "a big car")
    'a big car'

    >>> icontains("abc", ["a big car", "apple", "banana", "cab"])
    ['a big car']

    Parameter:
    ----------
    keywords : str
        Kata kunci yang ingin dicocokkan.
    texts : str | list
        Teks tunggal atau daftar teks yang akan dicek.

    Return:
    -------
    str | list | None
        - Jika 'texts' berupa string → mengembalikan teks itu sendiri jika cocok, None jika tidak.
        - Jika 'texts' berupa list → mengembalikan daftar teks yang cocok.
    """
    # Jika hanya satu teks (string tunggal)
    if isinstance(texts, str):
        return texts if _icontains(keywords, texts) else None

    # Jika daftar teks
    if isinstance(texts, list):
        return [text for text in texts if _icontains(keywords, text)]
