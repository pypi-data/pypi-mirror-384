from .doc_server import DocServer
from .doc_store import DocStore

app = DocServer(store=DocStore()).app

__all__ = ["app"]
