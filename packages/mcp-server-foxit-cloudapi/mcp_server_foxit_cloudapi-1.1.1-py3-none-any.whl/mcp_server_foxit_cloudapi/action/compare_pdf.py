import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_compare, request_task, save_file
from ..common.util import is_path


compare_pdf_input_schema = {
    "type": "object",
    "properties": {
        "basePath": {"type": "string", "description": "基准PDF文档的绝对路径或URL地址"},
        "comparePath": {"type": "string", "description": "比较PDF文档的绝对路径或URL地址"},
        "resultType": {"type": "string", "enum": ["json", "pdf"], "description": "结果类型", "default": "json"},
        "compareType": {"type": "string", "enum": ["all", "text"], "description": "比较类型", "default": "all"},
    },
    "required": ["basePath", "comparePath"],
}


async def compare_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("compare_pdf")
    logger.info(f"CALL TOOL compare_pdf, args: {args}, env: {env}")

    validate(args, compare_pdf_input_schema)
    args["resultType"] = args.get("resultType", "json")
    args["compareType"] = args.get("compareType", "all")

    res = request_document_compare({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    prefix_name = os.path.splitext(os.path.basename(args["basePath"]))[0] if is_path(args["basePath"]) else "download"
    doc["value"] = f"{prefix_name}-compare_pdf.{args['resultType']}"

    result_path = save_file({"doc": doc, "path": args["basePath"]}, env)

    return [TextContent(type="text", text=f"PDF文档比较成功：{result_path}")]
