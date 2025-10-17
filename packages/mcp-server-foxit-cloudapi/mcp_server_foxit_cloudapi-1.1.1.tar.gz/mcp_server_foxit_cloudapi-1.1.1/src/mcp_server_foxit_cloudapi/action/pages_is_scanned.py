import json
import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_pages_is_scanned, request_task, save_file


pages_is_scanned_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "pageRange": {
            "type": "string",
            "description": "页面范围。文档中的页面可以按任何顺序引用，从开始或结束都可以。例如：1、2、3、7-9、all。如果未指定，则执行所有页面",
        },
    },
    "required": ["path"],
}


async def pages_is_scanned(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("pages_is_scanned")
    logger.info(f"CALL TOOL pages_is_scanned, args: {args}, env: {env}")

    validate(args, pages_is_scanned_input_schema)

    res = request_document_pages_is_scanned({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])

    def resultProcessor(data):
        percentage = data["taskInfo"].get("percentage")
        pages_is_scanned_result = data["taskInfo"].get("pagesIsScannedResult")
        if percentage == 100 and pages_is_scanned_result:
            return pages_is_scanned_result

    pages_is_scanned_result = await request_task(res, {"clientId": env["clientId"]}, resultProcessor)

    return [TextContent(type="text", text=f"PDF文档的扫描状态：{json.dumps(pages_is_scanned_result, indent=4, ensure_ascii=False)}")]
