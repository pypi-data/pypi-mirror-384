import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_flatten, request_task, save_file
from ..common.util import is_path


flatten_pdf_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "pageRange": {
            "type": "string",
            "description": "PDF文档的页面范围。文档中的页面可以按任何顺序引用，从开始或结束都可以。例如：1、2、3、7-9，全部。如果未指定，则执行所有页面",
            "default": "all",
        },
    },
    "required": ["path"],
}


async def flatten_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("flatten_pdf")
    logger.info(f"CALL TOOL flatten_pdf, args: {args}, env: {env}")

    validate(args, flatten_pdf_input_schema)
    args["pageRange"] = args.get("pageRange", "all")

    res = request_document_flatten({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-flatten_pdf.pdf"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档扁平化成功：{result_path}")]
