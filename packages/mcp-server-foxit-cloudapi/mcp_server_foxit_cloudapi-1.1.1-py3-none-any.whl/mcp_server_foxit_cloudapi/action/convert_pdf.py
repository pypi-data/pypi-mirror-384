import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_convert, request_task, save_file
from ..common.util import is_path


convert_pdf_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "format": {
            "type": "string",
            "enum": ["word", "excel", "ppt", "image", "text", "html"],
            "description": "转换后的文件类型",
            "default": "word",
        },
    },
    "required": ["path"],
}


async def convert_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("convert_pdf")
    logger.info(f"CALL TOOL convert_pdf, args: {args}, env: {env}")

    validate(args, convert_pdf_input_schema)
    args["format"] = args.get("format", "word")

    res = request_document_convert({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    ext_format_map = {
        "word": "docx",
        "excel": "xlsx",
        "ppt": "pptx",
        "image": "zip",
        "text": "txt",
        "html": "html",
    }
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-convert_pdf.{ext_format_map[args['format']]}"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档转换成功：{result_path}")]
