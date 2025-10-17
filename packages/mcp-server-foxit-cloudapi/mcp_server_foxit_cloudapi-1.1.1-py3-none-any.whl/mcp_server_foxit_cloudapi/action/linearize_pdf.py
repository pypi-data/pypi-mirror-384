import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_linearize, request_task, save_file
from ..common.util import is_path


linearize_pdf_input_schema = {
    "type": "object",
    "properties": {"path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"}},
    "required": ["path"],
}


async def linearize_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("linearize_pdf")
    logger.info(f"CALL TOOL linearize_pdf, args: {args}, env: {env}")

    validate(args, linearize_pdf_input_schema)

    res = request_document_linearize({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-linearize_pdf.pdf"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档线性化成功：{result_path}")]
