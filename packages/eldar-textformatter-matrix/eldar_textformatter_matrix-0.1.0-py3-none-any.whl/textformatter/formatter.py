def capitalize_words(text):
    """Bütün sözləri böyük hərflə başlayar."""
    return " ".join(word.capitalize() for word in text.split())

def remove_extra_spaces(text):
    """Artıq boşluqları təmizləyər."""
    return " ".join(text.split())

def to_snake_case(text):
    """Mətni snake_case formatına salar."""
    return text.lower().replace(" ", "_")

def to_camel_case(text):
    """Mətni camelCase formatına salar."""
    words = text.split()
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

def normalize(text):
    """Mətni kiçik hərflərə çevirib xüsusi simvolları çıxarar."""
    import re
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
