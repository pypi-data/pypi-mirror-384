from mielto.knowledge.reader.base import Reader
from mielto.knowledge.document.base import Document
from mielto.utils.common import generate_prefix_ulid
from typing import Union, Optional, List, IO, Any
from pathlib import Path


from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    PDFPlumberLoader,
    JSONLoader,
    Docx2txtLoader,
    UnstructuredFileLoader,
)
from mielto.knowledge.chunking.strategy import ChunkingStrategyType

from langchain_core.documents import Document as LangchainDocument


class LangchainFileReader(Reader):
    """Reader for Langchain files"""


    @classmethod
    def get_supported_chunking_strategies(self) -> List[ChunkingStrategyType]:
        """Get the list of supported chunking strategies for PDF readers."""
        return [
            ChunkingStrategyType.DOCUMENT_CHUNKER,
            ChunkingStrategyType.FIXED_SIZE_CHUNKER,
            ChunkingStrategyType.AGENTIC_CHUNKER,
            ChunkingStrategyType.SEMANTIC_CHUNKER,
            ChunkingStrategyType.RECURSIVE_CHUNKER
        ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_loader(self, file: Union[Path, IO[Any], str], password: Optional[str] = None):
        path = Path(file)
        
        if not path.exists():
                raise ValueError(f"File not found: {file}")
            
        extension = path.suffix.lower()
        
        if extension == ".txt":
            loader = TextLoader(str(path))
        elif extension == ".pdf":
            loader = PDFPlumberLoader(str(path))
        elif extension == ".csv":
            loader = CSVLoader(str(path))
        elif extension == ".json":
            loader = JSONLoader(str(path))
        elif extension in [".docx", ".doc", ".docs"]:
            loader = Docx2txtLoader(str(path))
        elif extension in [".md", ".html", ".pptx", ".xlsx", ".xls", ".xml", ".odt", ".epub", ".rtf"]:
            loader = UnstructuredFileLoader(str(path))
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        return loader
    
    def _build_chunked_documents(self, documents: List[Document]) -> List[Document]:
        chunked_documents: List[Document] = []
        for document in documents:
            chunked_documents.extend(self.chunk_document(document))
        return chunked_documents

    def _create_documents(self, documents: List[LangchainDocument], name: Optional[str] = None) -> List[Document]:
        docs =  [Document(
            name=name,
            id=document.id or generate_prefix_ulid("chunk"),
            content=document.page_content,
            meta_data=document.metadata
        ) for document in documents]

        if self.chunk:
            return self._build_chunked_documents(docs)
        return docs

    def read(self, file: Union[Path, IO[Any], str], name: Optional[str] = None, password: Optional[str] = None) -> List[Document]:
        loader = self.get_loader(file, password)
        langchain_docs = loader.load()
        return self._create_documents(langchain_docs, name=name)

    async def async_read(self, file:  Union[Path, IO[Any], str], name: Optional[str] = None, password: Optional[str] = None) -> List[Document]:
        loader = self.get_loader(file)
        langchain_docs = await loader.aload()
        return self._create_documents(langchain_docs, name=name)