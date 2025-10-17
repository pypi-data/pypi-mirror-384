import json
import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_pages_basic_info, request_task, save_file


pages_basic_info_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "pageRange": {"type": "string", "description": "页面范围。文档中的页面可以按任何顺序引用，从开始或结束都可以。例如：1、2、3、7-9、all。如果未指定，则执行所有页面"},
    },
    "required": ["path"],
}


async def pages_basic_info(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("pages_basic_info")
    logger.info(f"CALL TOOL pages_basic_info, args: {args}, env: {env}")

    validate(args, pages_basic_info_input_schema)

    res = request_document_pages_basic_info({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])

    def resultProcessor(data):
        percentage = data["taskInfo"].get("percentage")
        pages_info = data["taskInfo"].get("pagesInfo")
        if percentage == 100 and pages_info:
            return pages_info
    pages_info = await request_task(res, {"clientId": env["clientId"]}, resultProcessor)

    return [TextContent(type="text", text=f"PDF文档页面信息：{json.dumps(pages_info, indent=4, ensure_ascii=False)}")]
