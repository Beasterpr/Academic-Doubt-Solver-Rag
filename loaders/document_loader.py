import tempfile
import os

from langchain_community.document_loaders import (
    PyPDFLoader,
    WebBaseLoader,
    YoutubeLoader,
)

from langchain_text_splitters import RecursiveCharacterTextSplitter


# RAG LOADER

def load_documents(paths, urls):
    """Load documents from PDF paths and/or URLs for RAG indexing."""
    docs = []

    for p in paths:
        docs.extend(PyPDFLoader(p).load())

    if urls:
        u = [
            x.strip()
            for x in urls.split("\n")
            if x.strip()
        ]
        docs.extend(WebBaseLoader(u).load())

    return docs


def split_documents_rag(docs, chunk_size=700, chunk_overlap=150):
    """Split documents using RAG chunking settings."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(docs)


# REPORT LOADERS

def load_from_url(url: str):
    """Load content from a web URL."""
    loader = WebBaseLoader(url)
    return loader.load()


def load_from_youtube(url: str):
    """
    Load transcript from a YouTube video.

    add_video_info is intentionally False — YouTube's oEmbed endpoint
    returns HTTP 400 for many videos and the metadata is not needed
    for report generation.  We try English captions first, then fall
    back to auto-generated ones.
    """
    # Try manual captions first, then auto-generated
    for languages in (["en"], ["en-US"], ["en-GB"], None):
        try:
            kwargs = dict(add_video_info=False)
            if languages is not None:
                kwargs["language"] = languages
            loader = YoutubeLoader.from_youtube_url(url, **kwargs)
            docs = loader.load()
            if docs:
                return docs
        except Exception:
            continue

    # Final attempt with no language preference — raises clearly if transcripts are truly unavailable
    try:
        loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
        return loader.load()
    except Exception as e:
        raise ValueError(
            "Could not load YouTube transcript. "
            "Make sure the video has captions/subtitles enabled. "
            f"Original error: {e}"
        ) from e


def load_from_pdf(uploaded_file) -> list:
    """Accept a Streamlit UploadedFile object and load its pages."""
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
    finally:
        os.unlink(tmp_path)

    return docs
