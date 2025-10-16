from abc import ABC, abstractmethod
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Literal, Type
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from pgvector_template.core.document import (
    BaseDocument,
    BaseDocumentMetadata,
    BaseDocumentOptionalProps,
)
from pgvector_template.core.embedder import BaseEmbeddingProvider


logger = getLogger(__name__)


class BaseCorpusManagerConfig(BaseModel):
    """Base configuration for `Corpus` & `Document` management operations"""

    document_cls: Type[BaseDocument] = Field(...)
    """Document class **type** (not an instance). Must be subclass of `BaseDocument`."""
    embedding_provider: BaseEmbeddingProvider | None = Field(default=None)
    """Instance of `BaseEmbeddingProvider` child class. Acts as embedding provider for insert operations."""
    document_metadata_cls: Type[BaseDocumentMetadata] = Field(default=BaseDocumentMetadata)
    """Document metadata class **type** (not an instance). Must be subclass of BaseDocumentMetadata."""

    model_config = {"arbitrary_types_allowed": True}


@dataclass
class Corpus:
    """
    Serves as the return type for `BaseCorpusManager.get_full_corpus()`.

    Logical grouping of one or more documents (chunks) belonging to the same original source (corpus).
    Typically all documents in a corpus share the same `corpus_id` and are ordered by `chunk_index`.
    """

    corpus_id: UUID | str
    content: str
    metadata: dict[str, Any]  # e.g. source, tags, etc.
    documents: list[BaseDocument]


class BaseCorpusManager(ABC):
    """
    Template class for `Corpus` & `Document` management operations.
    Each instance should be able to handle multiple collections, of the same Corpus/Document type.
    For example, if the document class is Jira tickets, multiple teams should be able to share the same
    `CorpusManager` implementation, with a slightly different config.
    """

    @property
    def config(self) -> BaseCorpusManagerConfig:
        return self._cfg

    @property
    def document_metadata_class(self) -> Type[BaseDocumentMetadata]:
        """Returns the document metadata class, raising an error if it's not set."""
        return self.config.document_metadata_cls

    @property
    def embedding_provider(self) -> BaseEmbeddingProvider:
        """Returns the embedding provider, raising an error if it's not set."""
        if self.config.embedding_provider is None:
            raise ValueError("embedding_provider must be provided in config for this operation")
        return self.config.embedding_provider

    def __init__(
        self,
        session: Session,
        config: BaseCorpusManagerConfig,
    ) -> None:
        self.session = session
        self._cfg = config
        if not self.config.embedding_provider:
            logger.warning(
                "EmbeddingProvider not provided in config. Insertion will be unavailable."
            )

    def get_full_corpus(self, corpus_id: str, **kwargs) -> Corpus | None:
        """Reconstruct full corpus from its individual documents/chunks"""
        chunks = (
            self.session.query(self.config.document_cls)
            .filter(
                self.config.document_cls.corpus_id == corpus_id,
                self.config.document_cls.is_deleted == False,
            )
            .order_by(self.config.document_cls.chunk_index)
            .all()
        )

        if not chunks:
            return None

        content, metadata = self._join_documents(chunks)
        return Corpus(
            corpus_id=corpus_id,
            content=content,
            metadata=metadata,
            documents=chunks,
        )

    def insert_corpus(
        self,
        content: str,
        corpus_metadata: dict[str, Any],
        optional_props: BaseDocumentOptionalProps | None = None,
        corpus_id: UUID | str | None = None,
        update_if_exists: bool = True,
        **kwargs,
    ) -> int:
        """
        Insert a new `Corpus`, which will be split into 1-or-more `Document`s, depending on its length.
        Each `Document` chunk shall have its own embedding vector, but reference the parent corpus_id.

        Args:
            content: The text content to be inserted as a corpus
            corpus_metadata: Dictionary of metadata associated with the corpus
            optional_props: Optional properties for the documents (title, collection, etc.)

        Returns:
            int: The number of **documents** inserted for the provided corpus
        """
        if not corpus_id:
            corpus_id = uuid4()
        document_contents = self._split_corpus(content)
        document_embeddings = self.embedding_provider.embed_batch(document_contents)
        return self.insert_documents(
            corpus_id,
            document_contents,
            document_embeddings,
            corpus_metadata,
            optional_props,
            update_if_exists,
        )

    def insert_documents(
        self,
        corpus_id: UUID | str,
        document_contents: list[str],
        document_embeddings: list[list[float]],
        corpus_metadata: dict[str, Any],
        optional_props: BaseDocumentOptionalProps | None = None,
        update_if_exists: bool = True,
        **kwargs,
    ) -> int:
        """
        Insert a list of documents (usually from a chunked + embedded corpus).

        Args:
            corpus_id: UUID of the corpus these documents belong to
            document_contents: List of text content for each document
            document_embeddings: List of embedding vectors corresponding to each document
            corpus_metadata: Dictionary of metadata to associate with all documents
            optional_props: Optional properties for the documents (title, collection, etc.)

        Returns:
            int: The number of documents inserted (0 if input lists are empty)

        Raises:
            ValueError: If the length of document_contents doesn't match document_embeddings
        """
        self._validate_inputs(document_contents, document_embeddings)
        if len(document_contents) == 0:
            return 0

        documents_to_insert = self._create_documents(
            corpus_id, document_contents, document_embeddings, corpus_metadata, optional_props
        )

        if update_if_exists:
            self._delete_existing_corpus(corpus_id)

        self.session.add_all(documents_to_insert)
        self.session.commit()
        return len(documents_to_insert)

    def _validate_inputs(
        self, document_contents: list[str], document_embeddings: list[list[float]]
    ) -> None:
        """Validate that document contents and embeddings match in length"""
        if len(document_contents) != len(document_embeddings):
            raise ValueError("Number of embeddings does not match number of documents")

    def _create_documents(
        self,
        corpus_id: UUID | str,
        document_contents: list[str],
        document_embeddings: list[list[float]],
        corpus_metadata: dict[str, Any],
        optional_props: BaseDocumentOptionalProps | None,
    ) -> list[BaseDocument]:
        """Create document instances from the provided data"""
        documents = []
        for i, (content, embedding) in enumerate(zip(document_contents, document_embeddings)):
            chunk_md = self._extract_chunk_metadata(content)
            base_metadata = self.document_metadata_class(**(corpus_metadata | chunk_md))
            documents.append(
                self.config.document_cls.from_props(
                    corpus_id=corpus_id,
                    chunk_index=i,
                    content=content,
                    embedding=embedding,
                    metadata=base_metadata.model_dump(),
                    optional_props=optional_props,
                )
            )
        return documents

    def _delete_existing_corpus(self, corpus_id: UUID | str) -> None:
        """Delete all existing documents for the given corpus_id"""
        self.session.query(self.config.document_cls).filter(
            self.config.document_cls.corpus_id == corpus_id
        ).delete()

    def _split_corpus(self, content: str, **kwargs) -> list[str]:
        """
        **It is highly recommended to override this method.**
        Split a corpus' string content into smaller chunks.
        """
        if self.__class__ is not BaseCorpusManager:
            logger.warning(
                "Using default _split_corpus. Override this method to improve performance."
            )
        split_content = [content[i : i + 1024 * 4] for i in range(0, len(content), 1024 * 4)]
        return [c for c in split_content if len(c.strip()) > 0]

    def _join_documents(
        self, documents: list[BaseDocument], **kwargs
    ) -> tuple[str, dict[str, Any]]:
        """
        **It is highly recommended to override this method.**
        **This method should effectively reverse the `_split_corpus` method.**
        Join a list of documents back into a single corpus string.
        Return an instance of corpus metadata. This is a best effort, since not all properties in
        `BaseDocumentMetadata`/`document_metadata_cls` are relevant to the corpus.
        """
        if self.__class__ is not BaseCorpusManager:
            logger.warning(
                "Using default _join_documents. Override this method to improve functionality."
            )
        documents.sort(key=lambda d: d.chunk_index)  # type: ignore
        # since _split_corpus performs a simple split on every 1000 chars, we can simply call `join`
        corpus_content = "".join(d.content for d in documents)  # type: ignore
        corpus_metadata = self._infer_corpus_metadata(documents)
        return corpus_content, corpus_metadata

    def _extract_chunk_metadata(self, content: str, **kwargs) -> dict[str, Any]:
        """
        **It is highly recommended to override this method.**
        Extract metadata from a chunk of content, to be appended to corpus metadata.
        Note: returning a key-value pair here does NOT guarantee its inclusion when it's added to the database.
        """
        if self.__class__ is not BaseCorpusManager:
            logger.warning(
                "Using default _extract_chunk_metadata. It is highly recommended to override this method."
            )
        # this is simply an example. Since the document metadata that gets saved
        return {
            "chunk_length": len(content),
        }

    def _infer_corpus_metadata(self, documents: list[BaseDocument], **kwargs) -> dict[str, Any]:
        """
        **It is highly recommended to override this method.**
        **This method should be a best-effort reversal of `extract_chunk_metadata()`**
        Infer metadata for the corpus from the constituent `BaseDocument`s.
        """
        if self.__class__ is not BaseCorpusManager:
            logger.warning(
                "Using default _infer_corpus_metadata. It is highly recommended to override this method."
            )
        # merge all document.document_metadata together, and return
        merged = {}
        for d in documents:
            merged.update(d.document_metadata)  # type: ignore
        return merged
