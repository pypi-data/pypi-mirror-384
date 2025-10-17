import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_extract, request_task, save_file
from ..common.util import is_path


extract_pdf_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "mode": {
            "type": "string",
            "enum": ["extractImages", "extractText"],
            "description": "提取模式，extractText表示提取文本，extractImages表示提取图片",
            "default": "extractImages",
        },
        "pageRange": {
            "type": "string",
            "description": "提取页面范围，A、B和C以逗号分隔。A、B或C可以取数字，如99，也可以取范围，如1-30。如果为空，则提取整个文档",
        },
    },
    "required": ["path", "mode"],
}


async def extract_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("extract_pdf")
    logger.info(f"CALL TOOL extract_pdf, args: {args}, env: {env}")

    validate(args, extract_pdf_input_schema)
    args["pageRange"] = args.get("pageRange", "")

    res = request_document_extract({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    mode_ext_map = {
        "extractImages": "zip",
        "extractText": "txt",
    }
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-extract_pdf.{mode_ext_map[args['mode']]}"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档提取成功：{result_path}")]
