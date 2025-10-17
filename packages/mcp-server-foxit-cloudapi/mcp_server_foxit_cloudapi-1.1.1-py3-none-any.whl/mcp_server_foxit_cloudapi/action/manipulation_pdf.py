import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_manipulation, request_task, save_file
from ..common.util import is_path


manipulation_pdf_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "config": {
            "type": "object",
            "properties": {
                "pageAction": {"type": "string", "enum": ["delete", "rotate", "move"], "description": "页面操作类型"},
                "pages": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "操作的页码，如[0,1,2,3]，页面索引从0开始",
                },
                "angle": {"type": "number", "description": "页面旋转，0：0度，1：90度，2：180度，-1：270度"},
                "destination": {"type": "number", "description": "目标页码，如果'页面操作类型'是'移动'，它是必需的"},
            },
            "description": "PDF文档操作配置",
        },
    },
    "required": ["path", "config"],
}


async def manipulation_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("manipulation_pdf")
    logger.info(f"CALL TOOL manipulation_pdf, args: {args}, env: {env}")

    validate(args, manipulation_pdf_input_schema)

    res = request_document_manipulation({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-manipulation_pdf.pdf"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档操作成功：{result_path}")]
