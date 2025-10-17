import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_protect, request_task, save_file
from ..common.util import is_path


protect_pdf_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "passwordProtection": {
            "type": "object",
            "properties": {
                "userPassword": {"type": "string", "description": "用户密码"},
                "ownerPassword": {"type": "string", "description": "所有者密码"},
            },
            "description": "密码保护设置，必须至少设置一个密码",
        },
        "permission": {
            "type": "object",
            "properties": {
                "PRINT_LOW_QUALITY": {"type": "boolean", "description": "以正常模式打印PDF文档", "default": False},
                "PRINT_HIGH_QUALITY": {"type": "boolean", "description": "以高质量打印PDF文档", "default": False},
                "EDIT_CONTENT": {
                    "type": "boolean",
                    "description": "修改PDF内容。设置该值后，用户可以通过操作修改PDF文档的内容",
                    "default": False,
                },
                "EDIT_FILL_AND_SIGN_FORM_FIELDS": {
                    "type": "boolean",
                    "description": "填写PDF表格。如果设置了该值，用户可以填写交互式表单字段（包括签名字段）",
                    "default": False,
                },
                "EDIT_ANNOTATION": {
                    "type": "boolean",
                    "description": "操作文本注释和填写交互式表单字段。如果还设置了'修改PDF内容'值，则用户可以创建或修改交互式表单字段",
                    "default": False,
                },
                "EDIT_DOCUMENT_ASSEMBLY": {
                    "type": "boolean",
                    "description": "组装PDF文档。如果设置了这个值，就可以组装文档（插入、旋转或删除页面以及创建书签或缩略图），而不管是否设置了'修改PDF内容'值",
                    "default": False,
                },
                "COPY_CONTENT": {
                    "type": "boolean",
                    "description": "残疾的支持。如果设置了此值，用户可以提取文本和图形，以支持残疾用户的可访问性或用于其他目的",
                    "default": False,
                },
            },
            "description": "权限设置",
            "default": {},
        },
        "encryptionAlgorithm": {
            "type": "string",
            "enum": ["AES_128", "AES_256", "RC4"],
            "description": "加密算法",
            "default": "AES_128",
        },
    },
    "required": ["path", "passwordProtection"],
}


async def protect_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("protect_pdf")
    logger.info(f"CALL TOOL protect_pdf, args: {args}, env: {env}")

    validate(args, protect_pdf_input_schema)
    args["permission"] = args.get("permission", {})
    args["encryptionAlgorithm"] = args.get("encryptionAlgorithm", "AES_128")

    res = request_document_protect({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-protect_pdf.pdf"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档保护成功：{result_path}")]
