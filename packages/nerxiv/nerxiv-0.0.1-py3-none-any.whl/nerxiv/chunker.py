from abc import ABC, abstractmethod

import spacy
import spacy.cli
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

from nerxiv.logger import logger

# Lazy-loaded singletons
_SPACY_NLP = None
_SENTENCE_MODEL = None


def get_spacy_model():
    global _SPACY_NLP
    if _SPACY_NLP is None:
        try:
            _SPACY_NLP = spacy.load("en_core_web_sm", disable=["ner"])
        except OSError:
            spacy.cli.download("en_core_web_sm")
            _SPACY_NLP = spacy.load("en_core_web_sm", disable=["ner"])
    return _SPACY_NLP


def get_sentence_model():
    global _SENTENCE_MODEL
    if _SENTENCE_MODEL is None:
        _SENTENCE_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _SENTENCE_MODEL


class BaseChunker(ABC):
    """
    Abstract base class for chunking text into smaller parts for processing and avoiding the token limit of an LLM model.
    """

    def __init__(self, text: str = "", **kwargs):
        if not text:
            raise ValueError("`text` is required for chunking.")
        self.text = text
        self.logger = kwargs.get("logger", logger)

    @abstractmethod
    def chunk_text(self) -> list[Document]:
        """Chunk the text into smaller parts."""
        pass


class Chunker(BaseChunker):
    """
    Chunk text into smaller parts for processing and avoiding the token limit of an LLM model.
    """

    def chunk_text(
        self, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> list[Document]:
        """
        Chunk the text into smaller parts.
        This is done to avoid exceeding the token limit of the LLM.

        Args:
            chunk_size (int, optional): The size of each chunk. Defaults to 1000.
            chunk_overlap (int, optional): The overlap between chunks. Defaults to 200.

        Returns:
            list[Document]: The list of chunks as `Document` objects.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=True
        )

        # ! we define a list of `Document` objects in LangChain to use the `split_documents(pages)` method
        pages = [
            Document(
                page_content=self.text,
                metadata={"source": "nerxiv.chunker.Chunker"},
            )
        ]
        chunks = text_splitter.split_documents(pages)
        self.logger.info(f"Text chunked into {len(chunks)} fixed chunks.")
        return chunks


class SemanticChunker(BaseChunker):
    """Sentence-level semantic chunker using spaCy."""

    def __init__(self, text: str = "", **kwargs):
        super().__init__(text=text, **kwargs)
        self.nlp = get_spacy_model()

    def chunk_text(self) -> list[Document]:
        """
        Chunk the text into smaller parts based on semantic meaning using spaCy.

        Returns:
            list[Document]: The list of chunks as `Document` objects.
        """
        doc = self.nlp(self.text)
        chunks = []
        for sent in doc.sents:
            chunks.append(
                Document(
                    page_content=sent.text.strip(),
                    metadata={"source": "nerxiv.chunker.SemanticChunker"},
                )
            )
        self.logger.info(f"Text chunked into {len(chunks)} semantic chunks.")
        return chunks


class AdvancedSemanticChunker(BaseChunker):
    """KMeans-based semantic chunker using SentenceTransformer embeddings."""

    def __init__(self, text: str = "", **kwargs):
        super().__init__(text=text, **kwargs)
        self.model = get_sentence_model()

    def chunk_text(self, n_chunks: int = 10) -> list[Document]:
        """
        Chunk the text into smaller parts based on semantic meaning using KMeans clustering on sentence embeddings.

        Args:
            n_chunks (int, optional): The number of chunks for the text to be chunked. Defaults to 10.

        Returns:
            list[Document]: The list of chunks as `Document` objects.
        """
        nlp = get_spacy_model()
        doc = nlp(self.text)
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        # Adjust number of clusters: at most one per sentence (1 <= n_chunks <= len(sentences))
        n_chunks = max(min(n_chunks, len(sentences)), 1)

        # Fit KMeans to the sentence embeddings
        embeddings = self.model.encode(sentences, show_progress_bar=False)
        kmeans = KMeans(n_clusters=n_chunks, random_state=42)
        clusters = kmeans.fit_predict(embeddings)
        chunks = [[] for _ in range(n_chunks)]
        for i, cluster in enumerate(clusters):
            chunks[cluster].append(sentences[i])

        # Combine sentences in each cluster to form chunks
        final_chunks = [
            Document(
                page_content=" ".join(chunk),
                metadata={"source": "nerxiv.chunker.AdvancedSemanticChunker"},
            )
            for chunk in chunks
            if chunk
        ]
        self.logger.info(f"Text chunked into {len(final_chunks)} semantic chunks.")
        return final_chunks


_CHUNKER_MAP = {
    "Chunker": Chunker,
    "SemanticChunker": SemanticChunker,
    "AdvancedSemanticChunker": AdvancedSemanticChunker,
}
