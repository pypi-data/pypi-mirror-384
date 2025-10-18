import json
import logging
from typing import Any, Iterable, Literal

from fastapi import APIRouter, FastAPI, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .doc_store import DocStore
from .interface import (
    Block,
    BlockInput,
    Content,
    ContentBlockInput,
    ContentInput,
    Doc,
    DocInput,
    DocStoreInterface,
    Element,
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
    Value,
    ValueInput,
)

INJECT: Any = None
_global_index = 0


def route(
    method: Literal["GET", "POST", "PUT", "DELETE"],
    path: str,
    *,
    tags: list[str],
):
    global _global_index
    _global_index += 1

    def decorator(func):
        func._route_info = {
            "index": _global_index,
            "method": method,
            "path": path,
            "tags": tags,
        }
        return func

    return decorator


def iter_response(iterable: Iterable[dict]) -> Iterable[bytes]:
    for item in iterable:
        json_string = json.dumps(item, ensure_ascii=False)
        yield (json_string + "\n").encode("utf-8")


class DocServer(DocStoreInterface):
    def __init__(self, store: DocStore) -> None:
        super().__init__()
        self.store = store
        self.store_cache = {}
        self.app = FastAPI(title="DocStore API")
        self.logger = logging.getLogger(__name__)

        # self.app.add_exception_handler(Exception, self.exception_handler)
        self.app.middleware("http")(self.exception_middleware)

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Lookup routes
        routes = []
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, "_route_info"):
                route_info = getattr(attr, "_route_info")
                routes.append((route_info["index"], route_info, attr))

        # Register routes
        api_router = APIRouter(prefix="/api/v1")
        for _, route_info, endpoint in sorted(routes):
            api_router.add_api_route(
                path=route_info["path"],
                endpoint=endpoint,
                methods=[route_info["method"]],
                response_model=None,
                tags=route_info["tags"],
            )

        self.app.include_router(api_router)

    async def exception_middleware(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            return self.exception_handler(request, e)

    def exception_handler(self, _: Request, e: Exception):
        if isinstance(e, ElementNotFoundError):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": "ElementNotFoundError", "message": str(e)},
            )
        elif isinstance(e, ElementExistsError):
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"error": "ElementExistsError", "message": str(e)},
            )
        elif isinstance(e, PermissionError):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "PermissionError", "message": str(e)},
            )
        elif isinstance(e, ValueError):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "ValueError", "message": str(e)},
            )
        self.logger.error("Unhandled exception occurred", exc_info=e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "InternalServerError", "message": str(e)},
        )

    def get_store(self, req: Request) -> DocStore:
        username = req.headers.get("X-Username")
        if not username:
            username = "tmp"
        store = self.store_cache.get(username)
        if not store:
            store = self.store.impersonate(username)
            self.store_cache[username] = store
        return store

    @route("GET", "/docs/{doc_id}", tags=["docs"])
    def get_doc(self, doc_id: str, req: Request = INJECT) -> Doc:
        return self.get_store(req).get_doc(doc_id)

    @route("GET", "/docs/pdf-path/{pdf_path:path}", tags=["docs"])
    def get_doc_by_pdf_path(self, pdf_path: str, req: Request = INJECT) -> Doc:
        return self.get_store(req).get_doc_by_pdf_path(pdf_path)

    @route("GET", "/docs/pdf-hash/{pdf_hash:path}", tags=["docs"])
    def get_doc_by_pdf_hash(self, pdf_hash: str, req: Request = INJECT) -> Doc:
        return self.get_store(req).get_doc_by_pdf_hash(pdf_hash)

    @route("GET", "/pages/{page_id}", tags=["pages"])
    def get_page(self, page_id: str, req: Request = INJECT) -> Page:
        return self.get_store(req).get_page(page_id)

    @route("GET", "/pages/image-path/{image_path:path}", tags=["pages"])
    def get_page_by_image_path(self, image_path: str, req: Request = INJECT) -> Page:
        return self.get_store(req).get_page_by_image_path(image_path)

    @route("GET", "/layouts/{layout_id}", tags=["layouts"])
    def get_layout(self, layout_id: str, req: Request = INJECT) -> Layout:
        return self.get_store(req).get_layout(layout_id)

    @route("GET", "/pages/{page_id}/layouts/{provider}", tags=["layouts"])
    def get_layout_by_page_id_and_provider(self, page_id: str, provider: str, req: Request = INJECT) -> Layout:
        return self.get_store(req).get_layout_by_page_id_and_provider(page_id, provider)

    @route("GET", "/blocks/{block_id}", tags=["blocks"])
    def get_block(self, block_id: str, req: Request = INJECT) -> Block:
        return self.get_store(req).get_block(block_id)

    @route("GET", "/pages/{page_id}/super-block", tags=["blocks"])
    def get_super_block(self, page_id: str, req: Request = INJECT) -> Block:
        return self.get_store(req).get_super_block(page_id)

    @route("GET", "/contents/{content_id}", tags=["contents"])
    def get_content(self, content_id: str, req: Request = INJECT) -> Content:
        return self.get_store(req).get_content(content_id)

    @route("GET", "/blocks/{block_id}/contents/{version}", tags=["contents"])
    def get_content_by_block_id_and_version(self, block_id: str, version: str, req: Request = INJECT) -> Content:
        return self.get_store(req).get_content_by_block_id_and_version(block_id, version)

    @route("GET", "/values/{value_id}", tags=["values"])
    def get_value(self, value_id: str, req: Request = INJECT) -> Value:
        return self.get_store(req).get_value(value_id)

    @route("GET", "/elements/{elem_id}/values/{key}", tags=["values"])
    def get_value_by_elem_id_and_key(self, elem_id: str, key: str, req: Request = INJECT) -> Value:
        return self.get_store(req).get_value_by_elem_id_and_key(elem_id, key)

    @route("GET", "/tasks/{task_id}", tags=["tasks"])
    def get_task(self, task_id: str, req: Request = INJECT) -> Task:
        return self.get_store(req).get_task(task_id)

    @route("POST", "/distinct/{elem_type}/{field}", tags=["others"])
    def distinct_values(
        self,
        elem_type: ElemType,
        field: Literal["tags", "provider", "version"],
        query: dict | None = None,
        req: Request = INJECT,
    ) -> list[str]:
        return self.get_store(req).distinct_values(elem_type, field, query)

    @route("POST", "/stream/{elem_type}", tags=["others"])
    def find(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        skip: int | None = None,
        limit: int | None = None,
        req: Request = INJECT,
    ) -> Iterable[Element]:
        it = self.get_store(req).find(elem_type, query, query_from, skip, limit)
        return StreamingResponse(iter_response(it), media_type="text/plain; charset=utf8")  # type: ignore

    @route("POST", "/list/docs", tags=["docs"])
    def list_docs(
        self,
        query: dict | None = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        req: Request = INJECT,
    ) -> list[Doc]:
        it = self.get_store(req).find_docs(query, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/pages", tags=["pages"])
    def list_pages(
        self,
        query: dict | None = None,
        doc_id: str | None = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        req: Request = INJECT,
    ) -> list[Page]:
        it = self.get_store(req).find_pages(query, doc_id, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/layouts", tags=["layouts"])
    def list_layouts(
        self,
        query: dict | None = None,
        page_id: str | None = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        req: Request = INJECT,
    ) -> list[Layout]:
        it = self.get_store(req).find_layouts(query, page_id, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/blocks", tags=["blocks"])
    def list_blocks(
        self,
        query: dict | None = None,
        page_id: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
        req: Request = INJECT,
    ) -> list[Block]:
        it = self.get_store(req).find_blocks(query, page_id, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/contents", tags=["contents"])
    def list_contents(
        self,
        query: dict | None = None,
        page_id: str | None = None,
        block_id: str | None = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        req: Request = INJECT,
    ) -> list[Content]:
        it = self.get_store(req).find_contents(query, page_id, block_id, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/values", tags=["values"])
    def list_values(
        self,
        query: dict | None = None,
        elem_id: str | None = None,
        key: str | None = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        req: Request = INJECT,
    ) -> list[Value]:
        it = self.get_store(req).find_values(query, elem_id, key, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/list/tasks", tags=["tasks"])
    def list_tasks(
        self,
        query: dict | None = None,
        target: str | None = None,
        command: str | None = None,
        status: str | None = None,
        create_user: str | None = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        req: Request = INJECT,
    ) -> list[Task]:
        it = self.get_store(req).find_tasks(query, target, command, status, create_user, skip=skip, limit=limit)
        return list(it)

    @route("POST", "/count/{elem_type}", tags=["others"])
    def count(
        self,
        elem_type: ElemType,
        query: dict | list[dict] | None = None,
        query_from: ElemType | None = None,
        estimated: bool = False,
        req: Request = INJECT,
    ) -> int:
        return self.get_store(req).count(elem_type, query, query_from, estimated)

    ####################
    # WRITE OPERATIONS #
    ####################

    @route("PUT", "/elements/{elem_id}/tags/{tag}", tags=["tags"])
    def add_tag(self, elem_id: str, tag: str, req: Request = INJECT) -> None:
        self.get_store(req).add_tag(elem_id, tag)

    @route("DELETE", "/elements/{elem_id}/tags/{tag}", tags=["tags"])
    def del_tag(self, elem_id: str, tag: str, req: Request = INJECT) -> None:
        self.get_store(req).del_tag(elem_id, tag)

    @route("PUT", "/elements/{elem_id}/metrics/{name}", tags=["metrics"])
    def add_metric(self, elem_id: str, name: str, metric_input: MetricInput, req: Request = INJECT) -> None:
        self.get_store(req).add_metric(elem_id, name, metric_input)

    @route("DELETE", "/elements/{elem_id}/metrics/{name}", tags=["metrics"])
    def del_metric(self, elem_id: str, name: str, req: Request = INJECT) -> None:
        self.get_store(req).del_metric(elem_id, name)

    @route("PUT", "/elements/{elem_id}/values/{key}", tags=["values"])
    def insert_value(self, elem_id: str, key: str, value_input: ValueInput, req: Request = INJECT) -> Value:
        return self.get_store(req).insert_value(elem_id, key, value_input)

    @route("POST", "/elements/{target_id}/tasks", tags=["tasks"])
    def insert_task(self, target_id: str, task_input: TaskInput, req: Request = INJECT) -> Task:
        return self.get_store(req).insert_task(target_id, task_input)

    @route("POST", "/docs", tags=["docs"])
    def insert_doc(self, doc_input: DocInput, skip_ext_check: bool = False, req: Request = INJECT) -> Doc:
        return self.get_store(req).insert_doc(doc_input, skip_ext_check)

    @route("POST", "/pages", tags=["pages"])
    def insert_page(self, page_input: PageInput, req: Request = INJECT) -> Page:
        return self.get_store(req).insert_page(page_input)

    @route("PUT", "/pages/{page_id}/layouts/{provider}", tags=["layouts"])
    def insert_layout(
        self,
        page_id: str,
        provider: str,
        layout_input: LayoutInput,
        insert_blocks: bool = True,
        upsert: bool = False,
        req: Request = INJECT,
    ) -> Layout:
        return self.get_store(req).insert_layout(page_id, provider, layout_input, insert_blocks, upsert)

    @route("POST", "/pages/{page_id}/blocks", tags=["blocks"])
    def insert_block(self, page_id: str, block_input: BlockInput, req: Request = INJECT) -> Block:
        return self.get_store(req).insert_block(page_id, block_input)

    @route("POST", "/pages/{page_id}/blocks/batch", tags=["blocks"])
    def insert_blocks(self, page_id: str, blocks: list[BlockInput], req: Request = INJECT) -> list[Block]:
        return self.get_store(req).insert_blocks(page_id, blocks)

    @route("PUT", "/blocks/{block_id}/contents/{version}", tags=["contents"])
    def insert_content(
        self, block_id: str, version: str, content_input: ContentInput, upsert: bool = False, req: Request = INJECT
    ) -> Content:
        return self.get_store(req).insert_content(block_id, version, content_input, upsert)

    @route("PUT", "/pages/{page_id}/content-blocks-layouts/{provider}", tags=["layouts"])
    def insert_content_blocks_layout(
        self,
        page_id: str,
        provider: str,
        content_blocks: list[ContentBlockInput],
        upsert: bool = False,
        req: Request = INJECT,
    ) -> Layout:
        return self.get_store(req).insert_content_blocks_layout(page_id, provider, content_blocks, upsert)

    ###################
    # TASK OPERATIONS #
    ###################

    @route("POST", "/grab-new-tasks/{command}", tags=["tasks"])
    def grab_new_tasks(
        self,
        command: str,
        args: dict[str, Any] = {},
        create_user: str | None = None,
        num: int = 10,
        hold_sec: int = 3600,
        req: Request = INJECT,
    ) -> list[Task]:
        return self.get_store(req).grab_new_tasks(command, args, create_user, num, hold_sec)

    @route("POST", "/update-grabbed-task/{task_id}", tags=["tasks"])
    def update_grabbed_task(
        self,
        task_id: str,
        grab_time: int,
        status: Literal["done", "error", "skipped"],
        error_message: str | None = None,
        req: Request = INJECT,
    ):
        return self.get_store(req).update_grabbed_task(task_id, grab_time, status, error_message)


def main():
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="DocStore HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host address")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--measure-time", action="store_true", help="Enable time measurement")
    parser.add_argument("--disable-events", action="store_true", help="Disable events")
    args = parser.parse_args()

    print("Starting DocStore HTTP Server...")

    doc_store = None
    doc_store = DocStore(measure_time=args.measure_time, disable_events=args.disable_events)
    doc_server = DocServer(doc_store)

    uvicorn.run(
        doc_server.app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
    )


if __name__ == "__main__":
    main()
