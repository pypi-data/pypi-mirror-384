import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_create_from_html, request_task, save_file
from ..common.util import is_path


create_pdf_from_html_input_schema = {
    "type": "object",
    "properties": {
        "format": {
            "type": "string",
            "enum": ["url", "html", "htm", "shtml"],
            "description": "输入格式，如果是url，则url参数不能为空，否则path参数不能为空",
            "default": "url",
        },
        "path": {"type": "string", "description": "HTML文件的绝对路径或URL地址"},
        "url": {"type": "string", "description": "URL"},
        "config": {
            "type": "object",
            "properties": {
                "width": {"type": "number", "description": "页面宽度，该值必须大于16，默认值为900(单位为1/72英寸)"},
                "height": {"type": "number", "description": "页面高度，该值必须大于16，默认值为600(单位为1/72英寸)"},
                "rotate": {"type": "number", "description": "页面旋转，0：0度，1：90度，2：180度，3：270度"},
                "pageMode": {"type": "number", "description": "页面模式，0：单页，1：多页"},
                "pageScaling": {"type": "number", "description": "页面缩放，1：适应页面，2：适应内容"},
            },
            "description": "配置项",
        },
    },
    "required": ["format"],
}


async def create_pdf_from_html(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("create_pdf_from_html")
    logger.info(f"CALL TOOL create_pdf_from_html, args: {args}, env: {env}")

    validate(args, create_pdf_from_html_input_schema)

    res = request_document_create_from_html({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]}, times=120)
    if args["format"] == "url":
        prefix_name = "download"
    else:
        prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-create_pdf_from_html.pdf"

    result_path = save_file({"doc": doc, "path": args["url"] if args["format"] == "url" else args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档创建成功：{result_path}")]
