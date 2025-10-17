import logging
import os
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_document_watermark, request_task, save_file
from ..common.util import is_path


watermark_pdf_input_schema = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "PDF文档的绝对路径或URL地址"},
        "imagePath": {
            "type": "string",
            "description": "水印图片的绝对路径或URL地址，水印类型为imageObject时，内容不能为空",
        },
        "pageRange": {
            "type": "string",
            "description": "页面范围。文档中的页面可以按任何顺序引用，从开始或结束都可以。例如：1、2、3、7-9、all。如果未指定，则执行所有页面",
        },
        "type": {"type": "string", "description": "水印类型，支持值：textObject, imageObject"},
        "position": {
            "type": "number",
            "description": "水印位置，默认值为左上角，支持值：0：左上角，1：顶部居中，2：右上角，3：垂直居中靠左，4：居中，5：垂直居中靠右，6：左下角，7：底部居中，8：右下角",
        },
        "offsetX": {"type": "number", "description": "水印X轴偏移量，单位为pt，默认值为0"},
        "offsetY": {"type": "number", "description": "水印Y轴偏移量，单位为pt，默认值为0"},
        "flagOnTopOfPage": {"type": "number", "description": "水印在最上层，有效值：0：否，1：是，默认值为0"},
        "flagNoPrint": {"type": "number", "description": "水印不允许打印，有效值：0：否，1：是，默认值为0"},
        "flagInvisible": {"type": "number", "description": "水印不可见，有效值：0：否，1：是，默认值为0"},
        "scaleX": {"type": "number", "description": "水印X轴缩放比例，必须大于0.001", "default": 1},
        "scaleY": {"type": "number", "description": "水印Y轴缩放比例，必须大于0.001", "default": 1},
        "rotation": {"type": "number", "description": "水印旋转角度，默认值为0"},
        "opacity": {"type": "number", "description": "水印透明度，范围0-100，默认值为100"},
        "font": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "水印文本，水印类型为textObject时，内容不能为空"},
                "size": {"type": "number", "description": "水印字体大小，默认值为12"},
                "fontName": {"type": "string", "description": "水印字体名称，默认值为Helvetica"},
                "color": {"type": "string", "description": "水印字体颜色，默认值为#000000"},
                "style": {
                    "type": "number",
                    "description": "水印字体样式，默认值为正常，有效值：0：正常，1：下划线",
                },
                "alignment": {
                    "type": "number",
                    "description": "水印字体对齐方式，默认值为左对齐，有效值：0：左对齐，1：居中对齐，2：右对齐",
                },
                "lineSpace": {"type": "number", "description": "水印字体行间距，默认值为1.0"},
            },
            "description": "字体信息，水印类型为textObject时，内容不能为空",
            "required": ["text"],
        },
    },
    "required": ["path", "type", "scaleX", "scaleY"],
}


async def watermark_pdf(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("watermark_pdf")
    logger.info(f"CALL TOOL watermark_pdf, args: {args}, env: {env}")

    validate(args, watermark_pdf_input_schema)

    res = request_document_watermark({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])
    doc = await request_task(res, {"clientId": env["clientId"]})
    prefix_name = os.path.splitext(os.path.basename(args["path"]))[0] if is_path(args["path"]) else "download"
    doc["value"] = f"{prefix_name}-watermark_pdf.pdf"

    result_path = save_file({"doc": doc, "path": args["path"]}, env)

    return [TextContent(type="text", text=f"PDF文档添加水印成功：{result_path}")]
