import base64
import hashlib
import io
import random
import re
import time
import uuid
import warnings
from functools import cached_property, wraps
from typing import Any, Callable, Iterable, Literal, TypeVar

import numpy as np
import pymongo.errors
from bson.objectid import ObjectId
from PIL import Image
from pymongo import ReturnDocument
from pymongo.database import Database

from .interface import (
    Block,
    BlockInput,
    Content,
    ContentBlockInput,
    ContentInput,
    Doc,
    DocExistsError,
    DocInput,
    DocStoreInterface,
    ElementExistsError,
    ElementNotFoundError,
    ElemType,
    Layout,
    LayoutInput,
    MetricInput,
    Page,
    PageInput,
    Task,
    TaskInput,
    TaskMismatchError,
    Value,
    ValueInput,
)
from .io import read_file
from .kafka import KafkaWriter
from .mongodb import get_mongo_db
from .pdf_doc import PDFDocument
from .structs import ANGLE_OPTIONS, BLOCK_TYPES, CONTENT_FORMATS, ContentBlock
from .utils import get_username

Image.MAX_IMAGE_PIXELS = None


def encode_ndarray(array: np.ndarray) -> str:
    with io.BytesIO() as buffer:
        np.save(buffer, array, allow_pickle=False)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


def decode_ndarray(string: str) -> np.ndarray:
    with io.BytesIO(base64.b64decode(string)) as buffer:
        return np.load(buffer, allow_pickle=False)


def _get_docs_coll(db: Database):
    # {
    #   /* ID */
    #   "id": "doc-caa42891-d13b-4dbf-ab7c-d2d23f76d770", // the unique doc_id
    #
    #   "orig_path": "s3://bucket/path/to/document.docx",
    #   "orig_filesize": 245267,
    #   "orig_hash": "9b1c8ef1309b52a63d457b9fb54d33eaebddf456a489d8da474f742be56467d8",
    #
    #   "pdf_path": "s3://bucket/path/to/document_1.pdf", (Unique Index)
    #   "pdf_filesize": 223245,
    #   "pdf_hash": "640b453d6de9d7fa198c6612107865bf2809ad02cea9dc44694fb5c64bde3335", (Unique Index)
    #
    #   "num_pages": 8,
    #
    #   /* First Page Info */
    #   "page_width": 0,
    #   "page_height": 0,
    #
    #   /* metadata from the pdf file. */
    #   "metadata": {
    #     "title": "xxxx",
    #     "author": "xxxx"
    #   },
    #
    #   "tags": ["tag1", "tag2"],
    #
    #   "metrics": {
    #     "metric_name_1": 0.1,
    #     "metric_name_2": 2,
    #   },
    #
    #   "create_time": 1749031069945,
    #   "update_time": 1749031069945,
    # }
    coll_docs = db.get_collection("docs")
    coll_docs.create_index([("id", 1)], unique=True)
    coll_docs.create_index([("pdf_path", 1)], unique=True)
    coll_docs.create_index([("pdf_hash", 1)], unique=True)
    coll_docs.create_index([("tags", 1)])
    coll_docs.create_index([("metrics.$**", 1)])
    return coll_docs


def _get_pages_coll(db: Database):
    # {
    #   /* ID */
    #   "id": "page-aac0d7e4-d22d-4b08-a8e8-1be28f79bc06", // the unique page_id
    #
    #   "doc_id": "e52e94f9-704d-4c8c-b9fc-bb375df705cc", (Index)
    #   "page_idx": 0,
    #
    #   /* Image Info */
    #   "image_path": "s3://bucket/path/to/page-image.jpg", (Unique Index)
    #   "image_filesize": 134156,
    #   "image_hash": "19fca535abe1fefd8e478afaac2f3b42f1d64eeb9e719dfd3ecfeb9789d4fe12",
    #   "image_width": 0,
    #   "image_height": 0,
    #
    #   "tags": ["tag1", "tag2"],
    #
    #   "metrics": {
    #     "metric_name_1": 0.1,
    #     "metric_name_2": 2,
    #   },
    #
    #   /* Writable Fields */
    #   "labels": {
    #     "label_name": "label_value",
    #   },
    #   "create_time": 1749031069945,
    #   "update_time": 1749031069945,
    # }
    coll_pages = db.get_collection("pages")
    coll_pages.create_index([("id", 1)], unique=True)
    coll_pages.create_index([("image_path", 1)], unique=True)
    # coll_pages.create_index([("image_hash", 1)], unique=True)
    coll_pages.create_index([("doc_id", 1)])
    coll_pages.create_index([("tags", 1)])
    coll_pages.create_index([("metrics.$**", 1)])
    # TODO: page should have initial category fields.

    # page->layout->content,
    # can i use page's label to filter layout and content?
    # how to represent golden state.

    return coll_pages


def _get_layouts_coll(db: Database):
    # {
    #   /* ID */
    #   "id": "layout-2b239dce-9c61-4a5d-9e73-1fb6f145eafe", // the unique layout_id
    #
    #   /* Unique Index */
    #   "page_id": "aac0d7e4-d22d-4b08-a8e8-1be28f79bc06",
    #   "provider": "layout__xxx",
    #
    #   /* Layout Data */
    #   /* 使用多叉树，允许块嵌套任意级。 */
    #   "blocks": [
    #     {
    #       "parent_id": "aa193195-cc0a-44f5-be64-46bfef1e6fc3", // 表归属关系
    #       "prev_id": "1614e7f7-fdb8-4135-a8b7-f83391008ce6", // 表顺序关系
    #       "id": "09329d9b-db9d-4c89-a8af-19a179e92890",
    #       "type": "title",
    #       "bbox": "0.0000,0.0000,1.0000,1.0000",
    #       "angle": None,  # enum(None, 0, 90, 180, 270)
    #     },
    #     { ... },
    #     ...
    #   ],
    #   /* 记录块之间的关系 */
    #   "relations": [
    #     {
    #       "from": "070a408f-3d52-451c-8f95-4cf7a817bc20",
    #       "to": "1614e7f7-fdb8-4135-a8b7-f83391008ce6",
    #       "relation": "caption_of",
    #     },
    #     { ... },
    #     ...
    #   ],
    #
    #   "tags": ["tag1", "tag2"],
    #
    #   /* Statistics */
    #   "stats": {
    #
    #   },
    #   "create_time": 1749031069945,
    #   "update_time": 1749031069945,
    # }
    coll_layouts = db.get_collection("layouts")
    coll_layouts.create_index([("id", 1)], unique=True)
    coll_layouts.create_index([("page_id", 1), ("provider", 1)], unique=True)
    coll_layouts.create_index([("provider", 1)])
    coll_layouts.create_index([("tags", 1)])
    coll_layouts.create_index([("metrics.$**", 1)])
    return coll_layouts


def _get_blocks_coll(db: Database):
    # {
    #   /* ID */
    #   "id": "block-145f4ce9-8b22-4c8b-a448-e6546f8ebe5d", // the unique block_id
    #
    #   /* Unique Index */
    #   "page_id": "aac0d7e4-d22d-4b08-a8e8-1be28f79bc06",
    #   "type": "title",
    #   "bbox": "0.0000,0.0000,1.0000,1.0000",
    #   "angle": None,  # enum(None, 0, 90, 180, 270)
    #
    #   /* --- */
    #   "scores": {
    #     "provider_a": 1.0,
    #   },
    #
    #   "tags": ["tag1", "tag2"],
    #
    #   /* Writable Fields */
    #   "labels": {
    #     "label_name": "label_value",
    #   },
    #   "create_time": 1749031069945,
    #   "update_time": 1749031069945,
    # }
    coll_blocks = db.get_collection("blocks")
    coll_blocks.create_index([("id", 1)], unique=True)
    # TODO: uncomment when index built.
    # coll_blocks.create_index([("page_id", 1), ("type", 1), ("bbox", 1), ("angle", 1)], unique=True)
    coll_blocks.create_index([("tags", 1)])
    coll_blocks.create_index([("metrics.$**", 1)])
    return coll_blocks


def _get_contents_coll(db: Database):
    # {
    #   /* ID */
    #   "id": "content-01a0c73b-c25c-4d5b-a535-5b21c55c5fd3", // the unique content_id
    #
    #   /* Unique Index */
    #   "block_id": "145f4ce9-8b22-4c8b-a448-e6546f8ebe5d",
    #   "version": "gemini_2_5_pro",
    #
    #   /* Copied Fields */
    #   "page_id": "aac0d7e4-d22d-4b08-a8e8-1be28f79bc06",
    #
    #   /* Main Fields */
    #   "format": "markdown",
    #   "content": "content of the block",
    #
    #   "tags": ["tag1", "tag2"],
    #
    #   /* Writable Fields */
    #   "labels": {
    #     "label_name": "label_value",
    #   },
    #   "create_time": 1749031069945,
    #   "update_time": 1749031069945,
    # }
    coll_contents = db.get_collection("contents")
    coll_contents.create_index([("id", 1)], unique=True)
    coll_contents.create_index([("block_id", 1), ("version", 1)], unique=True)
    coll_contents.create_index([("version", 1)])
    coll_contents.create_index([("page_id", 1)])
    coll_contents.create_index([("tags", 1)])
    coll_contents.create_index([("metrics.$**", 1)])
    return coll_contents


def _get_values_coll(db: Database):
    # {
    #   /* ID */
    #   "id": "value-01a0c73b-c25c-4d5b-a535-5b21c55c5fd3", // the unique value_id
    #
    #   /* Unique Index */
    #   "elem_id": "block-145f4ce9-8b22-4c8b-a448-e6546f8ebe5d",
    #   "key": "vit__embed_vector",
    #
    #   /* Main Fields */
    #   "type": "string",  # "string", "vector", (auto-set by insert_value())
    #   "value": "This is the value",
    #
    #   "create_time": 1749031069945,
    #   "update_time": 1749031069945,
    # }
    coll_values = db.get_collection("values")
    coll_values.create_index([("id", 1)], unique=True)
    coll_values.create_index([("elem_id", 1), ("key", 1)], unique=True)
    coll_values.create_index([("key", 1)])
    return coll_values


def _get_tasks_coll(db: Database):
    # {
    #   /* ID */
    #   "id": "task-dc99b06d-aeb2-4159-a4b9-a2bcf3c26b9b", // the unique task_id
    #   "target": "block-145f4ce9-8b22-4c8b-a448-e6546f8ebe5d",
    #   "command": "table_ext",
    #   "args": {
    #     "model_path": "/path/to/the/model"
    #   }
    #   "status": "new",  # "new", "done", "error", "skipped"
    #   "error_message": "error message if any",
    #
    #   "create_user": "zhangsan",
    #   "create_time": 1749031069945,
    #
    #   "update_user": "worker-1",
    #   "update_time": 1749031069945,
    #
    #   "grab_user": "worker-1",  # the worker who grabbed the task
    #   "grab_time": 1749031069945,  # when the task was grabbed by a worker
    # }
    coll_tasks = db.get_collection("tasks")
    coll_tasks.create_index([("id", 1)], unique=True)
    coll_tasks.create_index([("target", 1)])
    coll_tasks.create_index([("status", 1)])
    coll_tasks.create_index([("command", 1), ("status", 1), ("grab_time", 1)])
    coll_tasks.create_index([("create_user", 1)])
    return coll_tasks


def _get_known_users_coll(db: Database):
    coll_known_users = db.get_collection("known_users")
    coll_known_users.create_index([("name", 1)], unique=True)
    return coll_known_users


def _get_known_names_coll(db: Database):
    coll_known_names = db.get_collection("known_names")
    coll_known_names.create_index([("name", 1)], unique=True)
    return coll_known_names


def _get_task_shortcuts_coll(db: Database):
    coll_task_shortcuts = db.get_collection("task_shortcuts")
    coll_task_shortcuts.create_index([("name", 1)], unique=True)
    return coll_task_shortcuts


def _get_locks_coll(db: Database):
    # collection for distributed locks
    # {
    #   "key": "page-blocks:145f4ce9-8b22-4c8b-a448-e6546f8ebe5d",
    #   "version": 1,  # incremented on each write
    # }
    coll_locks = db.get_collection("locks")
    coll_locks.create_index([("key", 1)], unique=True)
    return coll_locks


class LockMismatchError(Exception):
    pass


class ShouldRetryError(Exception):
    pass


class VersionalLocker:
    def __init__(self, db: Database) -> None:
        self.coll_locks = _get_locks_coll(db)

    def read_ahead(self, key: str) -> int:
        """Read the lock version for a given key."""
        lock_data = self.coll_locks.find_one({"key": key})
        return lock_data["version"] if lock_data else 0

    def post_commit(self, key: str, version: int) -> None:
        """Commit the lock version for a given key."""
        if version == 0:
            try:
                self.coll_locks.insert_one({"key": key, "version": 1})
            except pymongo.errors.DuplicateKeyError:
                raise LockMismatchError(f"Lock for {key}::{version} expired.")
        else:
            result = self.coll_locks.update_one(
                {"key": key, "version": version},
                {"$set": {"version": version + 1}},
            )
            if result.modified_count == 0:
                raise LockMismatchError(f"Lock for {key}::{version} expired.")

    def run_with_lock(self, key: str, func: Callable[[], None]):
        """Run a function with a lock on the given key."""
        locked_version = self.read_ahead(key)
        func()
        self.post_commit(key, locked_version)


_KNOWN_FIELDS = {
    Doc: set(
        [
            "orig_path",
            "orig_filesize",
            "orig_filename",
            "orig_hash",
            "pdf_path",
            "pdf_filesize",
            "pdf_filename",
            "pdf_hash",
            "num_pages",
            "page_width",
            "page_height",
            "metadata",
            "tags",
        ]
    ),
    Page: set(
        [
            "doc_id",
            "page_idx",
            "image_path",
            "image_filesize",
            "image_hash",
            "image_width",
            "image_height",
            "image_dpi",
            "tags",
        ]
    ),
    Layout: set(
        [
            "page_id",
            "provider",
            "blocks",
            "relations",
            "tags",
        ]
    ),
    Block: set(
        [
            "page_id",
            "type",
            "bbox",
            "angle",
            "tags",
        ]
    ),
    Content: set(
        [
            "block_id",
            "version",
            "page_id",
            "format",
            "content",
            "tags",
        ]
    ),
    Value: set(
        [
            "elem_id",
            "key",
            "type",
            "value",
        ]
    ),
    Task: set(
        [
            "target",
            "command",
            "args",
            "status",
            "create_user",
            "update_user",
            "grab_user",
            "grab_time",
            "error_message",
        ]
    ),
}


_TMP_TYPE_MAPPING = {
    "text_block": "text",
    "code_txt": "code",
    "equation_isolated": "equation",
    "interline_equation": "equation",
    "equation_caption": "equation_number",
    "figure": "image",
    "figure_caption": "image_caption",
    "figure_footnote": "image_footnote",
    "reference": "ref_text",
    "need_mask": "unknown",
    "text_mask": "unknown",
    "table_mask": "unknown",
}


def _block_overlap(bbox_a: list[float], bbox_b: list[float]) -> float:
    """Calculate the overlap area ratio between two bounding boxes."""
    a_x1, a_y1, a_x2, a_y2 = bbox_a
    b_x1, b_y1, b_x2, b_y2 = bbox_b

    cross_x1 = max(a_x1, b_x1)
    cross_y1 = max(a_y1, b_y1)
    cross_x2 = min(a_x2, b_x2)
    cross_y2 = min(a_y2, b_y2)

    if cross_x1 >= cross_x2 or cross_y1 >= cross_y2:
        return 0.0
    area_a = (a_x2 - a_x1) * (a_y2 - a_y1)
    area_b = (b_x2 - b_x1) * (b_y2 - b_y1)
    area_cross = (cross_x2 - cross_x1) * (cross_y2 - cross_y1)
    area_union = area_a + area_b - area_cross
    assert area_union > 0, "Union area must be positive."
    return area_cross / area_union


def _measure_time(func):
    """Decorator to time a function execution."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        doc_store: DocStore | None = None
        if len(args) > 0 and isinstance(args[0], DocStore):
            doc_store = args[0]

        start_time = 0
        if doc_store and doc_store.measure_time:
            start_time = time.time()

        try:
            return func(*args, **kwargs)
        finally:
            if start_time > 0 and doc_store is not None:
                name = func.__name__
                times = doc_store.times
                elapsed = time.time() - start_time
                times[name] = elapsed + times.get(name, 0)

    return wrapper


T = TypeVar("T", bound=Doc | Page | Layout | Block | Content | Value | Task)
Q = TypeVar("Q", bound=Doc | Page | Layout | Block | Content | Value | Task)
TYPE = type[Doc | Page | Layout | Block | Content | Value | Task]

DocElement = Doc | Page | Layout | Block | Content
DOC_ELEM = TypeVar("DOC_ELEM", bound=DocElement)
DOC_ELEM_TYPES = (Doc, Page, Layout, Block, Content)


class DocEvent(dict):
    """Event class for document store events."""

    def __init__(
        self,
        elem_type: type[Doc | Page | Layout | Block | Content | Value],
        elem_id: str,
        event_type: Literal["insert", "add_tag", "del_tag"],
        event_user: str = "",
        layout_provider: str | None = None,
        block_type: str | None = None,
        content_version: str | None = None,
        tag_added: str | None = None,
        tag_deleted: str | None = None,
    ):
        assert elem_type in (Page, Layout, Block, Content, Doc, Value), f"Invalid element type {elem_type}."
        assert elem_id, "Element ID must be provided."
        assert event_type in ("insert", "add_tag", "del_tag"), f"Invalid event type {event_type}."

        self["elem_type"] = elem_type.__name__.lower()
        self["elem_id"] = elem_id
        self["event_type"] = event_type
        self["event_user"] = event_user
        if layout_provider is not None:
            self["layout_provider"] = layout_provider
        if block_type is not None:
            self["block_type"] = block_type
        if content_version is not None:
            self["content_version"] = content_version
        if tag_added is not None:
            self["tag_added"] = tag_added
        if tag_deleted is not None:
            self["tag_deleted"] = tag_deleted


class DocStore(DocStoreInterface):
    def __init__(self, measure_time=False, disable_events=False):
        db = get_mongo_db()
        self.coll_docs = _get_docs_coll(db)
        self.coll_pages = _get_pages_coll(db)
        self.coll_layouts = _get_layouts_coll(db)
        self.coll_blocks = _get_blocks_coll(db)
        self.coll_contents = _get_contents_coll(db)
        self.coll_values = _get_values_coll(db)
        self.coll_tasks = _get_tasks_coll(db)
        self.coll_known_users = _get_known_users_coll(db)
        self.coll_known_names = _get_known_names_coll(db)
        self.coll_task_shortcuts = _get_task_shortcuts_coll(db)
        self.locker = VersionalLocker(db)
        self.measure_time = measure_time
        self.times = {}

        self._event_sink = None
        if not disable_events:
            self._event_sink = KafkaWriter()

        self.username = get_username()
        self.writable = self.username in self.known_users
        self.user_info = self.known_users.get(self.username) or {}
        if not self.writable:
            warnings.warn(
                f"User [{self.username}] is not a known writer, read-only mode enabled.",
                UserWarning,
            )

    def impersonate(self, username: str) -> "DocStore":
        """Impersonate another user for this DocStore instance."""
        # use __new__ to bypass __init__
        new_store = DocStore.__new__(DocStore)
        new_store.coll_docs = self.coll_docs
        new_store.coll_pages = self.coll_pages
        new_store.coll_layouts = self.coll_layouts
        new_store.coll_blocks = self.coll_blocks
        new_store.coll_contents = self.coll_contents
        new_store.coll_values = self.coll_values
        new_store.coll_tasks = self.coll_tasks
        new_store.coll_known_users = self.coll_known_users
        new_store.coll_known_names = self.coll_known_names
        new_store.coll_task_shortcuts = self.coll_task_shortcuts
        new_store.locker = self.locker
        new_store.measure_time = self.measure_time
        new_store.times = {}
        new_store._event_sink = self._event_sink
        new_store.username = username
        new_store.writable = username in new_store.known_users
        new_store.user_info = new_store.known_users.get(username) or {}
        return new_store

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.flush()

    def _check_writable(self) -> None:
        """Check if the current user can write data to the DocStore."""
        if not self.writable:
            raise PermissionError(f"User [{self.username}] cannot write data to DocStore.")

    def _check_name(self, name_type: str, name_value: str) -> None:
        """Check if the provider or version is valid."""
        if not isinstance(name_value, str):
            raise ValueError(f"{name_type.capitalize()} must be a string.")
        if not re.match(r"^[a-zA-Z0-9_]+$", name_value):
            raise ValueError(f"{name_type.capitalize()} must contain only alphanumeric characters and underscores.")
        if not self.user_info.get("restricted"):
            if name_type == "tag" and name_value in self.known_tags:
                return  # Known tag, no need to check prefix
            if name_type == "metric" and name_value in self.known_metrics:
                return  # Known metric, no need to check prefix
        aliases = self.user_info.get("aliases") or []
        valid_prefixes = [f"{prefix}__" for prefix in [self.username, *aliases]]
        if any(name_value.startswith(prefix) for prefix in valid_prefixes):
            return  # Valid prefix
        raise ValueError(f"{name_type.capitalize()} must start with {valid_prefixes}.")

    def _new_id(self, elem_type: type[T]) -> str:
        """Generate a new unique ID for an element."""
        if elem_type not in (Doc, Page, Layout, Block, Content, Value, Task):
            raise ValueError(f"Unknown element type {elem_type}.")
        return f"{elem_type.__name__.lower()}-{uuid.uuid4()}"

    def _rand_num(self) -> int:
        """Generate a random number for an element."""
        return random.randint(0, (1 << 31) - 1)

    def _get_type(self, type_name: str) -> TYPE:
        type_name = type_name.lower()
        if type_name in ("page", "pages"):
            return Page
        elif type_name in ("layout", "layouts"):
            return Layout
        elif type_name in ("block", "blocks"):
            return Block
        elif type_name in ("content", "contents"):
            return Content
        elif type_name in ("doc", "docs"):
            return Doc
        elif type_name in ("value", "values"):
            return Value
        elif type_name in ("task", "tasks"):
            return Task
        else:
            raise ValueError(f"Unknown element type {type_name}.")

    def _get_coll(self, elem_type: ElemType | type[T]):
        if elem_type == Page or elem_type == "page":
            return self.coll_pages
        elif elem_type == Layout or elem_type == "layout":
            return self.coll_layouts
        elif elem_type == Block or elem_type == "block":
            return self.coll_blocks
        elif elem_type == Content or elem_type == "content":
            return self.coll_contents
        elif elem_type == Doc or elem_type == "doc":
            return self.coll_docs
        elif elem_type == Value or elem_type == "value":
            return self.coll_values
        elif elem_type == Task or elem_type == "task":
            return self.coll_tasks
        else:
            raise ValueError(f"Unknown element type {elem_type}.")

    def _get_elem_type_by_id(self, elem_id: str):
        if elem_id.startswith("page-"):
            return Page
        elif elem_id.startswith("layout-"):
            return Layout
        elif elem_id.startswith("block-"):
            return Block
        elif elem_id.startswith("content-"):
            return Content
        elif elem_id.startswith("doc-"):
            return Doc
        elif elem_id.startswith("value-"):
            return Value
        elif elem_id.startswith("task-"):
            return Task
        # fallback to block
        return Block

    def _dump_block(self, block_data: dict) -> dict:
        """Dump bbox in block data."""
        if "angle" not in block_data:
            block_data["angle"] = None

        bbox = block_data.get("bbox")
        if not bbox:
            bbox = [0.0, 0.0, 1.0, 1.0]
            block_data["type"] = "super"
        if isinstance(bbox, (list, tuple)):
            x1, y1, x2, y2 = bbox
            block_data["bbox"] = f"{x1:.4f},{y1:.4f},{x2:.4f},{y2:.4f}"
            return block_data
        if isinstance(bbox, str):
            return block_data
        raise ValueError("bbox must be a string or a list of floats.")

    def _parse_block(self, block_data: dict) -> dict:
        """Parse bbox in block data."""
        # TODO: temp code
        type = block_data.get("type")
        if type and _TMP_TYPE_MAPPING.get(type):
            block_data["type"] = _TMP_TYPE_MAPPING[type]

        if "angle" not in block_data:
            block_data["angle"] = None

        bbox = block_data.get("bbox")
        if not bbox:
            block_data["bbox"] = [0.0, 0.0, 1.0, 1.0]
            block_data["type"] = "super"
            return block_data
        if isinstance(bbox, str):
            block_data["bbox"] = list(map(float, bbox.split(",")))
            return block_data
        if isinstance(bbox, (list, tuple)):
            return block_data
        raise ValueError("bbox must be a string or a list of floats.")

    @_measure_time
    def _dump_elem(self, elem_type: type[T], elem_data: dict) -> dict:
        """Pre-process element data before insertion."""
        if elem_type == Block:
            elem_data = self._dump_block(elem_data)
        elif elem_type == Layout:
            blocks = elem_data.get("blocks") or []
            elem_data["blocks"] = [self._dump_elem(Block, b) for b in blocks]
        return elem_data

    @_measure_time
    def _parse_elem(self, elem_type: type[T], elem_data: dict) -> T:
        """Post-process element data after retrieval or insertion."""
        _id: ObjectId | None = elem_data.pop("_id", None)  # Hide MongoDB's _id

        if "create_time" not in elem_data and _id is not None:
            elem_data["create_time"] = int(_id.generation_time.timestamp() * 1000)
        if "update_time" not in elem_data and elem_data.get("create_time"):
            elem_data["update_time"] = elem_data["create_time"]

        if elem_type == Block:
            elem_data = self._parse_block(elem_data)
        elif elem_type == Layout:
            blocks = elem_data.get("blocks") or []
            elem_data["blocks"] = [self._parse_elem(Block, b) for b in blocks]
        elif elem_type == Content:
            elem_data["format"] = elem_data.get("format", "text")
        if isinstance(elem_data, elem_type) and elem_data._store is self:
            return elem_data
        return elem_type(elem_data, self)

    @_measure_time
    def _try_get_elem(self, elem_type: type[T], query: dict) -> T | None:
        """Try to get an element by its type and query, return None if not found."""
        coll = self._get_coll(elem_type)
        elem_data = coll.find_one(query)
        if elem_data is not None:
            elem_data = self._parse_elem(elem_type, elem_data)
        return elem_data

    @_measure_time
    def _get_elem(self, elem_type: type[T], query: dict) -> T:
        """Get an element by its type and query, raise ValueError if not found."""
        elem_data = self._try_get_elem(elem_type, query)
        if elem_data is None:
            raise ElementNotFoundError(f"{elem_type.__name__} with {query} not found.")
        return elem_data

    @_measure_time
    def _insert_elem(self, elem_type: type[T], elem_data: dict) -> T | None:
        """Insert a new element into the database."""
        self._check_writable()

        if not isinstance(elem_data, dict):
            raise ValueError(f"{elem_type.__name__} data must be a dictionary.")
        if "id" in elem_data:
            raise ValueError(f"{elem_type.__name__} data should not contains 'id' field.")

        known_fields = _KNOWN_FIELDS.get(elem_type, set())
        unknown_fields = [k for k in elem_data.keys() if k not in known_fields]
        if unknown_fields:
            raise ValueError(f"{elem_type.__name__} data has unknown fields: {unknown_fields}.")

        for tag in elem_data.get("tags") or []:
            self._check_name("tag", tag)

        coll = self._get_coll(elem_type)

        now = int(time.time() * 1000)
        elem_data["id"] = self._new_id(elem_type)
        elem_data["rid"] = self._rand_num()
        elem_data["create_time"] = now
        elem_data["update_time"] = now

        elem_data = self._dump_elem(elem_type, elem_data)

        try:
            coll.insert_one(elem_data)
        except pymongo.errors.DuplicateKeyError:
            return None

        if self._event_sink is not None and elem_type != Task:
            event_data = DocEvent(
                elem_type=elem_type,  # type: ignore
                elem_id=elem_data["id"],
                event_type="insert",
                event_user=self.username,
                layout_provider=elem_data.get("provider") if elem_type == Layout else None,
                block_type=elem_data.get("type") if elem_type == Block else None,
                content_version=elem_data.get("version") if elem_type == Content else None,
            )
            self._event_sink.write(event_data)

        if elem_type in DOC_ELEM_TYPES:
            for tag in elem_data.get("tags") or []:
                self.add_tag(elem_data["id"], tag)

        return self._parse_elem(elem_type, elem_data)

    @_measure_time
    def _upsert_elem(self, elem_type: type[T], query: dict, elem_data: dict) -> T:
        """Upsert an element into the database."""
        self._check_writable()

        if elem_type not in (Layout, Content):
            raise ValueError(f"Only Layout and Content can be upsert, not {elem_type.__name__}.")
        if not isinstance(query, dict) or not query:
            raise ValueError("query must be a non-empty dictionary.")
        if not isinstance(elem_data, dict):
            raise ValueError(f"{elem_type.__name__} update data must be a dictionary.")
        if "id" in elem_data:
            raise ValueError(f"{elem_type.__name__} data should not contains 'id' field.")

        for key, val in query.items():
            if key in elem_data and elem_data.pop(key) != val:
                raise ValueError(f"Query key '{key}' value '{val}' does not match with update data.")

        known_fields = _KNOWN_FIELDS.get(elem_type, set())
        merged_fields = set(query.keys()).union(elem_data.keys())
        unknown_fields = [k for k in merged_fields if k not in known_fields]
        if unknown_fields:
            raise ValueError(f"{elem_type.__name__} data has unknown fields: {unknown_fields}.")

        for tag in elem_data.get("tags") or []:
            self._check_name("tag", tag)

        coll = self._get_coll(elem_type)

        now = int(time.time() * 1000)
        insert_data = {}
        insert_data["id"] = self._new_id(elem_type)
        insert_data["rid"] = self._rand_num()
        insert_data["create_time"] = now
        insert_data.update(query)

        elem_data["update_time"] = now
        elem_data = self._dump_elem(elem_type, elem_data)

        result_data = coll.find_one_and_update(
            query,
            {
                "$set": elem_data,
                "$setOnInsert": insert_data,
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        if self._event_sink is not None:
            event_data = DocEvent(
                elem_type=elem_type,  # type: ignore
                elem_id=result_data["id"],
                event_type="insert",
                event_user=self.username,
                layout_provider=result_data.get("provider") if elem_type == Layout else None,
                block_type=result_data.get("type") if elem_type == Block else None,
                content_version=result_data.get("version") if elem_type == Content else None,
            )
            self._event_sink.write(event_data)

        for tag in elem_data.get("tags") or []:
            self.add_tag(elem_data["id"], tag)

        return self._parse_elem(elem_type, result_data)

    @_measure_time
    def _try_insert_blocks(self, page_id: str, blocks: list[dict]) -> list[dict]:
        """Try to insert blocks for a page, return list of inserted blocks."""
        self._check_writable()

        if not blocks:
            return []

        lock_key = f"page-blocks:{page_id}"
        locked_version = self.locker.read_ahead(lock_key)

        existing_blocks = list(self.find_blocks(page_id=page_id))
        for block in blocks:
            block_cmp_bbox = [round(num, 4) for num in block["bbox"]]

            block_elem = None
            for e_block in existing_blocks:
                if (
                    e_block["type"] == block["type"]
                    and e_block.get("angle") == block.get("angle")
                    and _block_overlap(e_block["bbox"], block_cmp_bbox) > 0.99
                ):
                    block_elem = e_block
                    break
            if block_elem is not None:
                for tag in block.get("tags") or []:
                    if tag not in block_elem.tags:
                        block_elem.add_tag(tag)
            else:  # block_data is None, should insert
                insert_data = {
                    "page_id": page_id,
                    "bbox": block["bbox"],
                    "type": block["type"],
                    "angle": block.get("angle"),
                    **({"tags": block["tags"]} if "tags" in block else {}),
                }
                block_elem = self._insert_elem(Block, insert_data)
                if block_elem is None:
                    raise ShouldRetryError()
                existing_blocks.append(block_elem)

            block["id"] = block_elem["id"]
            block["bbox"] = block_elem["bbox"]
            block["type"] = block_elem["type"]
            block["angle"] = block_elem.get("angle")

        self.locker.post_commit(lock_key, locked_version)
        return blocks

    def _check_blocks(self, blocks: list[dict]) -> None:
        for block_data in blocks:
            if not isinstance(block_data, dict):
                raise ValueError("Each block must be a dictionary.")

            bbox = block_data.get("bbox")
            if bbox is None:
                raise ValueError("block_data must contain 'bbox'.")
            if isinstance(bbox, str):
                bbox = list(map(float, bbox.split(",")))
                block_data["bbox"] = bbox
            if not isinstance(bbox, (list, tuple)):
                raise ValueError("bbox must be a string or a list of floats.")
            if len(bbox) != 4:
                raise ValueError("bbox must contain exactly 4 float values.")
            if not all(isinstance(x, (int, float)) for x in bbox):
                raise ValueError("bbox values must be integers or floats.")
            if any(not (0.0 <= x <= 1.0) for x in bbox):
                raise ValueError("bbox values must be in the range [0.0, 1.0].")
            if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                raise ValueError("bbox values are invalid: x1 >= x2 or y1 >= y2.")

            block_type = block_data.get("type")
            if not block_type:
                raise ValueError("block_data must contain 'type'.")
            if block_type not in BLOCK_TYPES:
                raise ValueError(f"unknown block type: {block_type}.")

            block_angle = block_data.get("angle")
            if block_angle not in ANGLE_OPTIONS:
                raise ValueError(f"Invalid angle: {block_angle}. Must be one of {ANGLE_OPTIONS}.")

            if block_type == "super":
                if bbox != [0.0, 0.0, 1.0, 1.0]:
                    raise ValueError("Super block must have bbox [0.0, 0.0, 1.0, 1.0].")
                if block_angle is not None:
                    raise ValueError("Super block cannot have angle.")

    @_measure_time
    def _insert_blocks(self, page_id: str, blocks: list[dict]) -> list[dict]:
        """Insert blocks for a page, return list of inserted blocks."""
        self._check_writable()

        if not blocks:
            return []

        self._check_blocks(blocks)

        retries = 0
        while True:
            try:
                return self._try_insert_blocks(page_id, blocks)
            except (LockMismatchError, ShouldRetryError) as e:
                retries += 1
                if retries >= 100:
                    raise
                if retries >= 10:
                    print(f"{type(e).__name__} after {retries} retries, retrying...")

    def _normalize_unstored_blocks(self, blocks: list[dict]) -> list[dict]:
        """Normalize unstored blocks by ensuring they have IDs and valid bbox."""
        self._check_blocks(blocks)

        for block in blocks:
            if block.get("id"):
                raise ValueError(f"Block data should not contains 'id' field.")
            if block.pop("tags", None):
                raise ValueError(f"Unstored block should not contains 'tags' field.")
            if block.pop("page_id", None):
                raise ValueError(f"Unstored block should not contains 'page_id' field.")
            if block.pop("content", None) is not None:
                raise ValueError(f"Unstored block should not contains 'content' field.")

            known_fields = _KNOWN_FIELDS.get(Block, set())
            unknown_fields = [k for k in block.keys() if k not in known_fields]
            if unknown_fields:
                raise ValueError(f"Block data has unknown fields: {unknown_fields}.")

            block["bbox"] = [round(num, 4) for num in block["bbox"]]
            block["angle"] = block.get("angle")
            block["id"] = self._new_id(Block)

        return blocks

    ##############
    # PROPERTIES #
    ##############

    @cached_property
    def known_users(self) -> dict[str, dict]:
        users = {}
        for user in self.coll_known_users.find({}):
            user.pop("_id", None)
            name = user.pop("name", None)
            if name:
                users[name] = user
        return users

    @cached_property
    def known_tags(self) -> set[str]:
        tags = set()
        for item in self.coll_known_names.find({"type": "tag"}):
            if item.get("name"):
                tags.add(item["name"])
        return tags

    @cached_property
    def known_metrics(self) -> set[str]:
        metrics = set()
        for item in self.coll_known_names.find({"type": "metric"}):
            if item.get("name"):
                metrics.add(item["name"])
        return metrics

    @cached_property
    def task_shortcuts(self) -> dict[str, dict]:
        shortcuts = {}
        for shortcut in self.coll_task_shortcuts.find({}):
            shortcut.pop("_id", None)
            name = shortcut.pop("name", None)
            if name:
                shortcuts[name] = shortcut
        return shortcuts

    ###################
    # READ OPERATIONS #
    ###################

    @_measure_time
    def get_doc(self, doc_id: str) -> Doc:
        """Get a doc by its ID."""
        return self._get_elem(Doc, {"id": doc_id})

    @_measure_time
    def get_doc_by_pdf_path(self, pdf_path: str) -> Doc:
        """Get a doc by its PDF path."""
        return self._get_elem(Doc, {"pdf_path": pdf_path})

    @_measure_time
    def get_doc_by_pdf_hash(self, pdf_hash: str) -> Doc:
        """Get a doc by its PDF sha256sum hex-string."""
        return self._get_elem(Doc, {"pdf_hash": pdf_hash.lower()})

    @_measure_time
    def get_page(self, page_id: str) -> Page:
        """Get a page by its ID."""
        return self._get_elem(Page, {"id": page_id})

    @_measure_time
    def get_page_by_image_path(self, image_path: str) -> Page:
        """Get a page by its image path."""
        return self._get_elem(Page, {"image_path": image_path})

    @_measure_time
    def get_layout(self, layout_id: str) -> Layout:
        """Get a layout by its ID."""
        return self._get_elem(Layout, {"id": layout_id})

    @_measure_time
    def get_layout_by_page_id_and_provider(self, page_id: str, provider: str) -> Layout:
        """Get a layout by its page ID and provider."""
        return self._get_elem(Layout, {"page_id": page_id, "provider": provider})

    @_measure_time
    def get_block(self, block_id: str) -> Block:
        """Get a block by its ID."""
        return self._get_elem(Block, {"id": block_id})

    @_measure_time
    def get_super_block(self, page_id: str) -> Block:
        """Get the super block for a page."""
        # TODO: temp code
        super_block = self._try_get_elem(Block, {"page_id": page_id, "type": ""})
        if super_block is not None:
            return super_block
        # new code
        super_block = self._try_get_elem(Block, {"page_id": page_id, "type": "super"})
        if super_block is not None:
            return super_block

        if not self.try_get_page(page_id):
            raise ElementNotFoundError(f"Page with ID {page_id} does not exist.")

        return self.insert_block(page_id, {"type": "super", "bbox": [0.0, 0.0, 1.0, 1.0]})

    @_measure_time
    def get_content(self, content_id: str) -> Content:
        """Get a content by its ID."""
        return self._get_elem(Content, {"id": content_id})

    @_measure_time
    def get_content_by_block_id_and_version(self, block_id: str, version: str) -> Content:
        """Get a content by its block ID and version."""
        return self._get_elem(Content, {"block_id": block_id, "version": version})

    @_measure_time
    def get_value(self, value_id: str) -> Value:
        """Get a value by its ID."""
        return self._get_elem(Value, {"id": value_id})

    @_measure_time
    def get_value_by_elem_id_and_key(self, elem_id: str, key: str) -> Value:
        """Get a value by its element ID and key."""
        return self._get_elem(Value, {"elem_id": elem_id, "key": key})

    @_measure_time
    def get_task(self, task_id: str) -> Task:
        """Get a task by its ID."""
        return self._get_elem(Task, {"id": task_id})

    @_measure_time
    def distinct_values(
        self,
        elem_type: ElemType | type[T],
        field: Literal["tags", "provider", "version"],
        query: dict | None = None,
    ) -> list[str]:
        """Get distinct values of a field for a given element type."""
        coll = self._get_coll(elem_type)
        return [v for v in coll.distinct(field, query) if v]

    def find(
        self,
        elem_type: ElemType | type[T],
        query: dict | list[dict] | None = None,
        query_from: ElemType | type[Q] | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> Iterable[T]:
        query = query or {}
        query_type = query_from or elem_type

        is_pipeline = isinstance(query, list)
        if query_type != elem_type and not is_pipeline:
            raise ValueError("query_from can only be used in pipeline query.")

        if is_pipeline:
            pipeline = [*query]
            if len(pipeline) > 0 and pipeline[0].get("$from"):
                query_type = self._get_type(pipeline[0]["$from"])
                pipeline = pipeline[1:]
            if skip is not None:
                pipeline.append({"$skip": skip})
            if limit is not None:
                pipeline.append({"$limit": limit})
            coll = self._get_coll(query_type)
            cursor = coll.aggregate(pipeline, maxTimeMS=86400000, batchSize=1000)
        else:  # normal query
            coll = self._get_coll(query_type)
            cursor = coll.find(query, max_time_ms=86400000, batch_size=1000)
            if skip is not None:
                cursor = cursor.skip(skip)
            if limit is not None:
                cursor = cursor.limit(limit)
        parse_type = elem_type
        if isinstance(elem_type, str):
            parse_type = self._get_type(elem_type)
        for layout in cursor:
            yield self._parse_elem(parse_type, layout)  # type: ignore

    @_measure_time
    def count(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        estimated: bool = False,
    ) -> int:
        """Count elements of a specific type matching the query."""
        query = query or {}
        query_type = query_from or elem_type

        is_pipeline = isinstance(query, list)
        if query_type != elem_type and not is_pipeline:
            raise ValueError("query_from can only be used in pipeline query.")

        if estimated and not query:
            coll = self._get_coll(query_type)
            return coll.estimated_document_count()

        if not is_pipeline:
            coll = self._get_coll(query_type)
            return coll.count_documents(query)

        pipeline = [*query]
        if len(pipeline) > 0 and pipeline[0].get("$from"):
            query_type = self._get_type(pipeline[0]["$from"])
            pipeline = pipeline[1:]
        pipeline.append({"$group": {"_id": 1, "n": {"$sum": 1}}})

        coll = self._get_coll(query_type)
        return int(next(coll.aggregate(pipeline))["n"])

    ####################
    # WRITE OPERATIONS #
    ####################

    @_measure_time
    def add_tag(self, elem_id: str, tag: str) -> None:
        """Add tag to an element."""
        self._check_writable()
        self._check_name("tag", tag)
        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)
        elem_data = coll.find_one_and_update(
            {"id": elem_id},
            {
                "$addToSet": {"tags": tag},
                "$set": {"update_time": now},
            },
        )
        if elem_data is None:
            return
        if tag.startswith("task__") and len(tag) > 6:
            # TODO: ensure the command is known
            shortcut_name = tag[6:].strip("_")
            shortcut = self.task_shortcuts.get(shortcut_name) or {}
            self.insert_task(
                elem_id,
                {
                    "command": shortcut.get("command") or shortcut_name,
                    "args": shortcut.get("args") or {},
                },
            )
        if self._event_sink is not None and elem_type != Task:
            event_data = DocEvent(
                elem_type=elem_type,  # type: ignore
                elem_id=elem_id,
                event_type="add_tag",
                event_user=self.username,
                layout_provider=elem_data.get("provider") if elem_type == Layout else None,
                block_type=elem_data.get("type") if elem_type == Block else None,
                content_version=elem_data.get("version") if elem_type == Content else None,
                tag_added=tag,
            )
            self._event_sink.write(event_data)

    @_measure_time
    def del_tag(self, elem_id: str, tag: str) -> None:
        """Delete tag from an element."""
        self._check_writable()
        self._check_name("tag", tag)
        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)
        elem_data = coll.find_one_and_update(
            {"id": elem_id},
            {
                "$pull": {"tags": tag},
                "$set": {"update_time": now},
            },
        )
        if elem_data is None:
            return
        if self._event_sink is not None and elem_type != Task:
            event_data = DocEvent(
                elem_type=elem_type,  # type: ignore
                elem_id=elem_id,
                event_type="del_tag",
                event_user=self.username,
                layout_provider=elem_data.get("provider") if elem_type == Layout else None,
                block_type=elem_data.get("type") if elem_type == Block else None,
                content_version=elem_data.get("version") if elem_type == Content else None,
                tag_deleted=tag,
            )
            self._event_sink.write(event_data)

    @_measure_time
    def add_metric(self, elem_id: str, name: str, metric_input: MetricInput) -> None:
        """Add a metric to an element."""
        self._check_writable()
        self._check_name("metric", name)

        if not isinstance(metric_input, dict):
            raise ValueError("metric_input must be a dictionary.")
        value = metric_input.get("value")
        if not isinstance(value, (int, float)):
            raise ValueError("value must be an integer or a float.")

        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)

        if not coll.update_one(
            {"id": elem_id, "metrics": None},
            {"$set": {"metrics": {name: value}, "update_time": now}},
        ).modified_count:
            coll.update_one(
                {"id": elem_id},
                {"$set": {f"metrics.{name}": value, "update_time": now}},
            )

    @_measure_time
    def del_metric(self, elem_id: str, name: str) -> None:
        """Delete a metric from an element."""
        self._check_writable()
        self._check_name("metric", name)
        elem_type = self._get_elem_type_by_id(elem_id)
        coll = self._get_coll(elem_type)
        now = int(time.time() * 1000)
        coll.update_one(
            {"id": elem_id},
            {
                "$unset": {f"metrics.{name}": ""},
                "$set": {"update_time": now},
            },
        )

    @_measure_time
    def insert_doc(self, doc_input: DocInput, skip_ext_check=False) -> Doc:
        """Insert a new doc into the database."""
        self._check_writable()
        if not isinstance(doc_input, dict):
            raise ValueError("doc_input must be a dictionary.")
        doc_data = dict(doc_input)

        orig_path = doc_data.get("orig_path")
        if orig_path is not None:
            if not isinstance(orig_path, str):
                raise ValueError("orig_path must be a string.")
            if not orig_path.startswith(("/", "s3://")):
                raise ValueError("orig_path must start with '/' or 's3://'.")
            if not orig_path.lower().endswith((".docx", ".doc", ".pptx", ".ppt")):
                raise ValueError("orig_path must end with .docx, .doc, .pptx, or .ppt.")

        pdf_path = doc_data.get("pdf_path")
        if not pdf_path:
            raise ValueError("doc_data must contain 'pdf_path'.")
        if not isinstance(pdf_path, str):
            raise ValueError("pdf_path must be a string.")
        if not pdf_path.startswith(("/", "s3://")):
            raise ValueError("pdf_path must start with '/' or 's3://'.")
        if not skip_ext_check and not pdf_path.lower().endswith(".pdf"):
            raise ValueError("pdf_path must end with .pdf.")
        if self.try_get_doc_by_pdf_path(pdf_path):
            raise DocExistsError(
                message=f"doc with pdf path {pdf_path} already exists.",
                pdf_path=pdf_path,
                pdf_hash=None,
            )

        if orig_path is not None:
            orig_content = read_file(orig_path, allow_local=False)
            doc_data["orig_filesize"] = len(orig_content)
            doc_data["orig_hash"] = hashlib.sha256(orig_content).hexdigest()

        pdf_content = read_file(pdf_path, allow_local=False)
        pdf_document = PDFDocument(pdf_content)
        if pdf_document.num_pages <= 0:
            raise ValueError(f"PDF document at {pdf_path} has no pages.")

        doc_data["pdf_filesize"] = len(pdf_content)
        doc_data["pdf_hash"] = hashlib.sha256(pdf_content).hexdigest()
        doc_data["num_pages"] = pdf_document.num_pages
        doc_data["page_width"] = pdf_document.page_width
        doc_data["page_height"] = pdf_document.page_height
        doc_data["metadata"] = pdf_document.metadata

        result = self._insert_elem(Doc, doc_data)
        if result is None:
            raise DocExistsError(
                message=f"doc with pdf path {pdf_path} already exists.",
                pdf_path=pdf_path,
                pdf_hash=doc_data["pdf_hash"],
            )
        return result

    @_measure_time
    def insert_page(self, page_input: PageInput) -> Page:
        """Insert a new page into the database."""
        self._check_writable()
        if not isinstance(page_input, dict):
            raise ValueError("page_input must be a dictionary.")
        page_data = dict(page_input)

        doc_id = page_data.pop("doc_id", None)
        page_idx = page_data.pop("page_idx", None)

        if doc_id is not None:
            if not isinstance(doc_id, str):
                raise ValueError("doc_id must be a string.")
            if not doc_id:
                raise ValueError("doc_id must not be empty.")
            if page_idx is None:
                raise ValueError("page_idx must be provided if doc_id is provided.")
            if not isinstance(page_idx, int) or page_idx < 0:
                raise ValueError("page_idx must be a non-negative integer.")
            doc = self.try_get_doc(doc_id)
            if doc is None:
                raise ValueError(f"Doc with ID {doc_id} does not exist.")
            if page_idx >= doc.num_pages:
                raise ValueError(f"page_idx {page_idx} is beyond {doc.num_pages} pages for doc {doc_id}.")
            page_data["doc_id"] = doc_id
            page_data["page_idx"] = page_idx

        image_path = page_data.get("image_path")
        if not image_path:
            raise ValueError("page_data must contain 'image_path'.")
        if not isinstance(image_path, str):
            raise ValueError("image_path must be a string.")
        if not image_path.startswith(("/", "s3://")):
            raise ValueError("image_path must start with '/' or 's3://'.")
        if not image_path.lower().endswith((".jpg", ".jpeg", ".png")):
            raise ValueError("image_path must end with .jpg, .jpeg, or .png.")
        if self.try_get_page_by_image_path(image_path):
            raise ElementExistsError(f"page with image path {image_path} already exists.")

        image_content = read_file(image_path, allow_local=False)
        image = Image.open(io.BytesIO(image_content))
        image = image.convert("RGB")  # Some broken image may raise.

        page_data["image_filesize"] = len(image_content)
        page_data["image_hash"] = hashlib.sha256(image_content).hexdigest()
        page_data["image_width"] = image.width
        page_data["image_height"] = image.height

        result = self._insert_elem(Page, page_data)
        if result is None:
            raise ElementExistsError(f"page with image path {image_path} already exists.")
        return result

    @_measure_time
    def insert_layout(self, page_id: str, provider: str, layout_input: LayoutInput, insert_blocks=True, upsert=False) -> Layout:
        """Insert a new layout into the database."""
        self._check_writable()
        self._check_name("provider", provider)

        if not page_id:
            raise ValueError("page_id must be provided.")
        if not isinstance(layout_input, dict):
            raise ValueError("layout_data must be a dictionary.")
        layout_data = dict(layout_input)

        blocks = layout_data.get("blocks")
        if not isinstance(blocks, list):
            raise ValueError("layout_data must contain 'blocks' as a list.")
        if not self.try_get_page(page_id):
            raise ValueError(f"Page with ID {page_id} does not exist.")
        if not upsert and self.try_get_layout_by_page_id_and_provider(page_id, provider):
            raise ElementExistsError(f"Layout for page {page_id} with provider {provider} already exists.")

        if insert_blocks:
            layout_data["blocks"] = self._insert_blocks(page_id, blocks)
        else:  # use unstored blocks
            layout_data["blocks"] = self._normalize_unstored_blocks(blocks)

        if upsert:
            query = {"page_id": page_id, "provider": provider}
            return self._upsert_elem(Layout, query, layout_data)

        layout_data["page_id"] = page_id
        layout_data["provider"] = provider

        result = self._insert_elem(Layout, layout_data)
        if result is None:
            raise ElementExistsError(
                f"Layout for page {page_id} with provider {provider} already exists.",
            )
        return result

    @_measure_time
    def insert_block(self, page_id: str, block_input: BlockInput) -> Block:
        """Insert a new block for a page."""
        self._check_writable()

        if not page_id:
            raise ValueError("page_id must be provided.")
        if not isinstance(block_input, dict):
            raise ValueError("block_input must be a dictionary.")
        if not self.try_get_page(page_id):
            raise ValueError(f"Page with ID {page_id} does not exist.")

        block = self._insert_blocks(page_id, [block_input])[0]  # type: ignore
        block["page_id"] = page_id
        return self._parse_elem(Block, block)

    @_measure_time
    def insert_blocks(self, page_id: str, blocks: list[BlockInput]) -> list[Block]:
        """Insert multiple blocks for a page."""
        self._check_writable()

        if not page_id:
            raise ValueError("page_id must be provided.")
        if not isinstance(blocks, list):
            raise ValueError("blocks must be a list of dictionaries.")
        if not blocks:
            return []
        if not self.try_get_page(page_id):
            raise ValueError(f"Page with ID {page_id} does not exist.")

        inserted_blocks = self._insert_blocks(page_id, blocks)  # type: ignore
        for block in inserted_blocks:
            block["page_id"] = page_id
        return [self._parse_elem(Block, block) for block in inserted_blocks]

    @_measure_time
    def insert_content(self, block_id: str, version: str, content_input: ContentInput, upsert=False) -> Content:
        """Insert a new content for a block."""
        self._check_writable()
        self._check_name("version", version)

        if not block_id:
            raise ValueError("block_id must be provided.")
        if not isinstance(content_input, dict):
            raise ValueError("content_input must be a dictionary.")
        content_data = dict(content_input)

        format = content_data.get("format")
        if not format:
            raise ValueError("content_data must contain 'format'.")
        if format not in CONTENT_FORMATS:
            raise ValueError(f"unknown content format: {format}.")

        content = content_data.get("content")
        if content is None:
            raise ValueError("content_data must contain 'content'.")
        if not isinstance(content, str):
            raise ValueError("content must be a string.")

        block_data = self.try_get_block(block_id)
        if not block_data:
            raise ValueError(f"Block with ID {block_id} does not exist.")
        content_data["page_id"] = block_data.get("page_id")

        if upsert:
            query = {"block_id": block_id, "version": version}
            return self._upsert_elem(Content, query, content_data)

        content_data["block_id"] = block_id
        content_data["version"] = version

        result = self._insert_elem(Content, content_data)
        if result is None:
            raise ElementExistsError(
                f"Content for block {block_id} with version {version} already exists.",
            )
        return result

    @_measure_time
    def insert_value(self, elem_id: str, key: str, value_input: ValueInput) -> Value:
        """Insert a new value for a target."""
        self._check_writable()
        self._check_name("key", key)
        if not isinstance(value_input, dict):
            raise ValueError("value_input must be a dictionary.")

        value = value_input.get("value")
        if not isinstance(value, (str, np.ndarray)):
            raise ValueError("value must be a string or numpy array.")

        value_type = "str"
        if isinstance(value, np.ndarray):
            value_type = "ndarray"
            value = encode_ndarray(value)

        value_data = {
            "elem_id": elem_id,
            "key": key,
            "type": value_type,
            "value": value,
        }
        result = self._insert_elem(Value, value_data)
        if result is None:
            raise ElementExistsError(f"Value for element {elem_id} and key {key} already exists.")
        return result

    @_measure_time
    def insert_task(self, target_id: str, task_input: TaskInput) -> Task:
        """Insert a new task into the database."""
        self._check_writable()
        if not target_id:
            raise ValueError("target_id must be provided.")
        if not isinstance(task_input, dict):
            raise ValueError("task_input must be a dictionary.")
        command = task_input.get("command")
        if not isinstance(command, str) or not command:
            raise ValueError("command must be a non-empty string.")
        args = task_input.get("args", {})
        if not isinstance(args, dict):
            raise ValueError("args must be a dictionary.")
        if any(not isinstance(k, str) for k in args.keys()):
            raise ValueError("All keys in args must be strings.")

        if command.startswith("ddp."):
            # command is a handler path.
            command, args["path"] = "handler", command

        task_data = {
            "target": target_id,
            "command": command,
            "args": args,
            "status": "new",
            "create_user": self.username,
            "grab_time": 0,
        }

        result = self._insert_elem(Task, task_data)
        assert result is not None, "Task insertion failed, should not happen."
        return result

    @_measure_time
    def insert_content_blocks_layout(
        self,
        page_id: str,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
    ) -> Layout:
        """Import content blocks and create a layout for a page."""
        self._check_writable()
        if not page_id:
            raise ValueError("page_id must be provided.")
        if not provider:
            raise ValueError("provider must be a non-empty string.")

        if not self.try_get_page(page_id):
            raise ValueError(f"Page with ID {page_id} does not exist.")
        if not upsert and self.try_get_layout_by_page_id_and_provider(page_id, provider):
            raise ElementExistsError(f"Layout for page {page_id} with provider {provider} already exists.")

        parsed_blocks: list[ContentBlock] = []
        for block in content_blocks:
            if not isinstance(block, dict):
                raise ValueError("Each content_block must be a dict.")
            parsed_blocks.append(ContentBlock(**block))

        blocks = [
            {
                "bbox": b.bbox,
                "type": b.type,
                "angle": b.angle,
                **({"score": b.score} if b.score is not None else {}),
                **({"tags": b.block_tags} if b.block_tags else {}),
            }
            for b in parsed_blocks
        ]
        inserted_blocks = self._insert_blocks(page_id, blocks)

        for c, block in zip(parsed_blocks, inserted_blocks):
            if c.content is not None:
                try:
                    content_input = ContentInput({"content": c.content, "format": c.format or "text"})
                    if c.content_tags:
                        content_input["tags"] = c.content_tags
                    self.insert_content(block["id"], provider, content_input, upsert=upsert)
                except ElementExistsError:
                    pass

        return self.insert_layout(page_id, provider, {"blocks": inserted_blocks}, upsert=upsert)

    ###################
    # TASK OPERATIONS #
    ###################

    @_measure_time
    def grab_new_task(
        self,
        command: str,
        args: dict[str, Any] = {},
        create_user: str | None = None,
        hold_sec=3600,
    ) -> Task | None:
        """Grab a new task for processing."""
        self._check_writable()
        if not isinstance(command, str) or not command:
            raise ValueError("command must be a non-empty string.")
        if hold_sec < 30:
            raise ValueError("hold_sec must be at least 30 seconds.")
        if any(not isinstance(k, str) for k in args.keys()):
            raise ValueError("All keys in args must be strings.")

        query = {"command": command, "status": "new"}
        for key, value in args.items():
            query[f"args.{key}"] = value

        if create_user is not None:
            if not isinstance(create_user, str) or not create_user:
                raise ValueError("create_user must be a non-empty string.")
            query["create_user"] = create_user

        grabbed_task = self.coll_tasks.find_one_and_update(
            filter={
                **query,
                "$expr": {
                    "$lt": [
                        "$grab_time",
                        {"$subtract": [{"$toLong": "$$NOW"}, hold_sec * 1000]},
                    ]
                },
            },
            update=[
                {
                    "$set": {
                        "grab_time": {"$toLong": "$$NOW"},
                        "grab_user": self.username,
                    }
                }
            ],
            return_document=ReturnDocument.AFTER,
        )
        if grabbed_task is None:
            return None
        return self._parse_elem(Task, grabbed_task)

    @_measure_time
    def grab_new_tasks(
        self,
        command: str,
        args: dict[str, Any] = {},
        create_user: str | None = None,
        num=10,
        hold_sec=3600,
    ) -> list[Task]:
        """Grab new tasks for processing."""
        grabbed_tasks = []
        for _ in range(num):
            task = self.grab_new_task(command, args, create_user, hold_sec)
            if task is None:
                break
            grabbed_tasks.append(task)
        return grabbed_tasks

    @_measure_time
    def update_grabbed_task(
        self,
        task_id: str,
        grab_time: int,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
    ):
        """Update a task after processing."""
        self._check_writable()
        if not task_id:
            raise ValueError("task ID must be provided.")
        if not grab_time:
            raise ValueError("grab_time must be provided.")
        if status not in ("done", "error", "skipped"):
            raise ValueError("status must be one of 'done', 'error', or 'skipped'.")
        if status == "error" and not error_message:
            raise ValueError("error_message must be provided if status is 'error'.")

        result = self.coll_tasks.update_one(
            {"id": task_id, "status": "new", "grab_time": grab_time},
            {
                "$set": {
                    "status": status,
                    **({"error_message": error_message} if error_message else {}),
                    "update_time": int(time.time() * 1000),
                    "update_user": self.username,
                },
            },
        )
        if result.modified_count == 0:
            raise TaskMismatchError(
                f"Task with ID {task_id} not found or already updated.",
            )

    def count_new_tasks(self) -> list[tuple[str, str, int]]:
        """Count tasks by command and status."""
        results = []
        for item in self.coll_tasks.aggregate(
            [
                {"$match": {"status": "new"}},
                {
                    "$group": {
                        "_id": {
                            "command": "$command",
                            "path": "$args.path",
                            "template": "$args.template",
                            "model_name": "$args.model_name",
                            "create_user": "$create_user",
                        },
                        "count": {"$sum": 1},
                    }
                },
            ],
            maxTimeMS=10000,
        ):
            group: dict = item["_id"]
            command = group["command"]
            if command == "handler" and group.get("path"):
                command = group["path"]
            other_args = []
            if group.get("template"):
                other_args.append(group["template"])
            if group.get("model_name"):
                other_args.append(group["model_name"])
            if other_args:
                command += f"({','.join(other_args)})"
            results.append((command, group["create_user"], item["count"]))

        results.sort()
        return results

    ##########
    # OTHERS #
    ##########

    def print_times(self) -> None:
        """Print the time taken for each operation."""
        if not self.measure_time:
            print("Time measurement is disabled.")
            return

        if not self.times:
            print("No operations were timed.")
            return

        print("Operation times:")
        for name, elapsed in sorted(self.times.items(), key=lambda x: x[1], reverse=True):
            print(f" - {name}: {elapsed:.4f} seconds")

    def flush(self) -> None:
        """Flush the database changes."""
        if self._event_sink is not None:
            self._event_sink.flush()


# use page-id-block-id ID format.
