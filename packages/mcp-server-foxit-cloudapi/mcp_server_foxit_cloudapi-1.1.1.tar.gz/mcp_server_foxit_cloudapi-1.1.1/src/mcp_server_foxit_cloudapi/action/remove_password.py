import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_remove_password, request_task, save_file
from ..common.util import is_path


remove_password_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "password": {
            "type": "string",
            "description": "PDF文档密码。如果PDF受所有者密码保护，则用户需要在该字段中使用所有者密码来取消文档安全性，否则用户需要传入用户密码来打开文档",
        },
    },
    "required": ["path", "password"],
}


async def remove_password(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("remove_password")
    logger.info(f"CALL TOOL remove_password, args: {args}, env: {env}")

    validate(args, remove_password_input_schema)

    res = request_document_remove_password({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-remove_password.pdf"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档密码移除成功：{result_path}")]
