import copy
import re
import Orange
from Orange.data import Domain, Table, StringVariable, ContinuousVariable
from chonkie import TokenChunker, WordChunker, SentenceChunker

def create_chunks(table, model, chunk_size=500, overlap=125, mode="words", progress_callback=None, argself=None):
    """
    Chunk the text contained in the column "content" of an input table, with the help of an embedding model.

    Parameters:
        table (Table): The input table to process
        model (SentenceTransformer): The embeddings model to process the text.
        mode (str): chunking mode

    Returns:
        out_data (Table): The data table with a column "Chunks" (and more rows if several chunks were obtained per text)
    """
    data = copy.deepcopy(table)

    # Définir la fonction de chunking selon le mode
    if mode == "tokens":
        chunk_function = chunk_tokens
    elif mode == "words":
        chunk_function = chunk_words
    elif mode == "sentence":
        chunk_function = chunk_sentences
    elif mode == "semantic":
        chunk_function = chunk_semantic
    elif mode == "markdown":
        chunk_function = chunk_markdown
    else:
        raise ValueError(f"Invalid mode: {mode}. Valid modes are: 'tokens', 'words', 'sentence', 'markdown', 'semantic'")

    #new_metas = [StringVariable("Chunks"), ContinuousVariable("Chunks index"), StringVariable("Metadata")]
    new_metas = list(data.domain.metas) + [StringVariable("Chunks"), ContinuousVariable("Chunks index"), StringVariable("Metadata")]
    new_domain = Domain(data.domain.attributes, data.domain.class_vars, new_metas)

    new_rows = []
    for i, row in enumerate(data):
        content = row["content"].value
        chunks, metadatas = chunk_function(content, tokenizer=model.tokenizer, chunk_size=chunk_size, chunk_overlap=overlap)
        # For each chunk in the chunked data
        for j, chunk in enumerate(chunks):
            # Build a new row with the previous data and the chunk
            if len(metadatas) == 0:
                new_metas_values = list(row.metas) + [chunk] + [j] + [""]
            else:
                new_metas_values = list(row.metas) + [chunk] + [j] + [metadatas[j]]
            new_instance = Orange.data.Instance(new_domain, [row[x] for x in data.domain.attributes] + [row[y] for y in data.domain.class_vars] + new_metas_values)
            new_rows.append(new_instance)

    return Table.from_list(domain=new_domain, rows=new_rows)


def chunk_tokens(content, tokenizer, chunk_size=512, chunk_overlap=128):
    chunker = TokenChunker(tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk(content)
    chunks = [chunk.text for chunk in chunks]
    return chunks, []

def chunk_words(content, tokenizer, chunk_size=300, chunk_overlap=100):
    chunker = WordChunker(tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = chunker.chunk(content)
    chunks = [chunk.text for chunk in chunks]
    return chunks, []

def chunk_sentences(content, tokenizer, chunk_size=500, chunk_overlap=125):
    chunker = SentenceChunker(tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                              min_sentences_per_chunk=1)
    chunks = chunker.chunk(content)
    chunks = [chunk.text for chunk in chunks]
    return chunks, []

def chunk_markdown(content, tokenizer=None, chunk_size=500, chunk_overlap=125):
    """
    Découpe un contenu Markdown en chunks :
    - Si des en-têtes Markdown (#, ##, ###...) existent : on respecte la hiérarchie
      et on inclut dans les métadonnées uniquement les titres de la branche courante.
    - Sinon : on délègue à chunk_words().

    Parameters
    ----------
    content : str
        Le contenu (Markdown ou texte brut).
    tokenizer : any
        Tokenizer utilisé par WordChunker si besoin.
    chunk_size : int
        Nombre max de mots par chunk.
    chunk_overlap : int
        Overlap (en mots) entre deux chunks consécutifs.

    Returns
    -------
    (chunks, metadatas) : tuple(list[str], list[str])
        chunks : segments de texte
        metadatas : hiérarchies de titres associées (chaînes " ; " séparées), vide si aucun titre.
    """
    if not content or not isinstance(content, str):
        return [], []

    header_regex = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
    matches = list(header_regex.finditer(content))

    # Cas SANS en-têtes : appel direct à chunk_words
    if not matches:
        chunks, _ = chunk_words(content, tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return chunks, [""] * len(chunks)

    # Cas AVEC en-têtes : extraire les sections (level, title, body)
    sections = []
    for i, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        sections.append((level, title, body))

    chunks, metadatas = [], []
    current_titles = {}

    for level, title, body in sections:
        # purge les niveaux >= level
        for l in list(current_titles.keys()):
            if l >= level:
                current_titles.pop(l, None)
        current_titles[level] = title

        metadata = " ; ".join(current_titles[lvl] for lvl in sorted(current_titles) if lvl <= level)

        # déléguer le découpage de body à chunk_words
        body_chunks, _ = chunk_words(body, tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        for ch in body_chunks:
            chunks.append(ch)
            metadatas.append(metadata)

    return chunks, metadatas

def chunk_semantic():
    pass