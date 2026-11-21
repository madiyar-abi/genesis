"""Public tool descriptions shared by the environment and baseline policies."""

TOOLS = [
    {"type": "list_records", "params": {"table": "ledger|invoices|payments|fx", "cursor": "null|str",
                                        "limit": "int<=50"},
     "returns": "{rows, next_cursor, total}; invoice rows omit line_items"},
    {"type": "get_record", "params": {"table": "ledger|invoices|payments|fx", "id": "str"},
     "returns": "{record}"},
    {"type": "get_document", "params": {"doc_id": "str"}, "returns": "{kind, document}"},
    {"type": "calculator", "params": {"expression": "str: + - * / ( ) and decimals only"},
     "returns": "{value}"},
    {"type": "submit", "params": {"findings": "{episode_id, findings:[...]}"}, "returns": "ends the episode"},
]
