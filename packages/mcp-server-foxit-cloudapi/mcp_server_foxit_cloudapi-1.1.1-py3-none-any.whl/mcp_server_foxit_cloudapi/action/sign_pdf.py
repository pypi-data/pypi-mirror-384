import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_sign, request_task, save_file
from ..common.util import is_path


sign_pdf_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "imagePath": {"type": "string", "description": "印章图片的绝对路径或URL地址"},
        "pageIndex": {"type": "number", "description": "添加印章页码，将放置签名的页索引（从1开始）", "default": 1},
        "signatureRect": {
            "type": "string",
            "description": "印章坐标位置，PDF坐标系，单位。格式：[left, bottom, right, top]",
            "default": "[0, 0, 100, 100]",
        },
        "certId": {"type": "string", "description": "证书ID，由apply_certificate工具生成"},
        "appearanceFlag": {
            "type": "string",
            "description": '外观标志，可选值：APFlagReason, APFlagSigningTime, APFlagLocation, APFlagSigner, APFlagImage, APFlagText。输入格式：["APFlagReason", "APFlagSigningTime"]',
        },
        "signer": {"type": "string", "description": "签名者名称"},
        "text": {"type": "string", "description": "签名文本内容"},
        "location": {"type": "string", "description": "签名地点"},
        "reason": {"type": "string", "description": "签名原因"},
        "contactInfo": {"type": "string", "description": "联系信息"},
    },
    "required": ["path", "pageIndex", "signatureRect", "certId"],
}


async def sign_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("sign_pdf")
    logger.info(f"CALL TOOL sign_pdf, args: {args}, env: {env}")

    validate(args, sign_pdf_input_schema)

    res = request_document_sign({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-sign_pdf.pdf"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档签名成功：{result_path}")]
