


# collection/index/table/type/schema/


class Storage:
    def __init__(self):
        self.data = {}

    def find_one(self, schema: str, query: dict):
        pass

    def insert_one(self, schema: str, doc: dict):
        "Insert if absent, otherwise raise exception"
        pass

    def update_one(self, schema: str, query: dict, update: dict):
        pass

    def find_one_and_update(self, schema: str, query: dict, update: dict):
        pass

    def find(self, schema: str, query: dict):
        pass

    def count(self, schema: str, query: dict) -> int:
        pass

    def distinct(self, schema: str, key: str, query: dict):
        pass



















# find_one
# find_one_and_update
# insert_one
# update_one
# find
# aggregate
# count_documents
estimated_document_count
distinct
