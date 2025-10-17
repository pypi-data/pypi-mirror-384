import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_split, request_task, save_file
from ..common.util import is_path


split_pdf_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "config": {
            "type": "object",
            "properties": {"pageCount": {"type": "number", "description": "拆分后的页数"}},
            "description": "配置项",
        },
    },
    "required": ["path", "config"],
}


async def split_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("split_pdf")
    logger.info(f"CALL TOOL split_pdf, args: {args}, env: {env}")

    validate(args, split_pdf_input_schema)

    res = request_document_split({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-split_pdf.zip"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档拆分成功：{result_path}")]
