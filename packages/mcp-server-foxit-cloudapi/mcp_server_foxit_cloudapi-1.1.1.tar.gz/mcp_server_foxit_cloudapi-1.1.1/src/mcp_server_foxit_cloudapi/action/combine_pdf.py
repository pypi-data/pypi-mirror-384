import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_combine, request_task, save_file
from ..common.util import is_path


combine_pdf_input_schema = {
    "type": "object",
    "properties": {
        "path": {
            "type": ["string", "array"],
            "items": {"type": "string"},
            "description": "压缩或归档文件的绝对路径或多个URL地址",
        },
        "config": {
            "type": "object",
            "properties": {
                "isAddBookmark": {"type": "boolean", "description": "是否添加书签"},
                "isAddTOC": {"type": "boolean", "description": "是否添加目录"},
                "isContinueMerge": {"type": "boolean", "description": "如果发生错误是否继续合并"},
                "isRetainPageNum": {"type": "boolean", "description": "是否保留页面逻辑号"},
                "bookmarkLevels": {
                    "type": "string",
                    "enum": ["0", "1", "2", "3", "4", "5"],
                    "description": "是否显示目录的等级",
                },
            },
            "description": "配置项",
            "default": {},
        },
    },
    "required": ["path"],
}


async def combine_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("combine_pdf")
    logger.info(f"CALL TOOL combine_pdf, args: {args}, env: {env}")

    validate(args, combine_pdf_input_schema)
    args["config"] = args.get("config", {})

    res = request_document_combine({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    if isinstance(args["path"], str):
        prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
        doc["value"] = f"{prefix_name}-combine_pdf.pdf"
    else:
        prefix_name = os.path.splitext(os.path.basename(args["path"][0]))[0] if is_path(args["path"][0]) else "download"
        doc["value"] = f"{prefix_name}-combine_pdf.pdf"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档合并成功：{result_path}")]
