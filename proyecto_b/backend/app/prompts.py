"""Prompts compartidos por el pipeline y por los scripts de benchmark/comparativa."""
CATEGORIES = ["politica", "economia", "deportes", "tecnologia", "cultura",
              "salud", "ciencia", "internacional", "otros"]
MAX_CHARS = 6000
SYS_CLASSIFY = 'Clasifica el articulo. Responde SOLO JSON: {"category": una de ' + str(CATEGORIES) + '}'
SYS_ENRICH = ('Extrae del articulo. Responde SOLO JSON: {"entities":[{"text":"","type":"PERSONA|ORG|LUGAR"}],'
              '"sentiment":"positivo|neutral|negativo","sentiment_score":-1.0 a 1.0}')
SEO_HINTS = ("", " MAS CORTO, maximo 140 caracteres.")

def sys_seo(hint: str = "") -> str:
    return ("Escribe un meta-description SEO en espanol, una sola frase, menos de 160 caracteres."
            + hint + " Responde solo la frase.")

def messages(task: str, text: str, hint: str = "") -> list[dict]:
    system = {"classify": SYS_CLASSIFY, "enrich": SYS_ENRICH, "seo": sys_seo(hint)}[task]
    return [{"role": "system", "content": system}, {"role": "user", "content": text[:MAX_CHARS]}]
