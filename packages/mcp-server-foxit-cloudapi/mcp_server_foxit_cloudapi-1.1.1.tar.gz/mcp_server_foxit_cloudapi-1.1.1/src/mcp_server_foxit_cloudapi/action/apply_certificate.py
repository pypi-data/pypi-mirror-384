import logging
from mcp.types import TextContent
from jsonschema import validate
from ..common.service import request_cert_apply, request_task, save_file


apply_certificate_input_schema = {
    "type": "object",
    "properties": {
        "certValid": {"type": "number", "description": "证书有效期，单位为年。最长5年，最短1年。默认值为1年", "default": 1},
        "agentName": {"type": "string", "description": "经办人名称"},
        "agentIdCard": {"type": "string", "description": "经办人身份证号码"},
        "agentPhone": {"type": "string", "description": "经办人手机号码"},
        "orgName": {"type": "string", "description": "企业组织名称"},
        "orgLegalPerson": {"type": "string", "description": "企业组织法定代表人"},
        "orgRegisterNo": {"type": "string", "description": "企业统一社会信用代码"},
        "orgLegalPersonIdCard": {"type": "string", "description": "法人证件号"},
    },
    "required": ["agentName", "agentIdCard", "agentPhone", "orgName", "orgLegalPerson", "orgRegisterNo", "orgLegalPersonIdCard"],
}


async def apply_certificate(args: dict, env: dict) -> list[TextContent]:
    logger = logging.getLogger("apply_certificate")
    logger.info(f"CALL TOOL apply_certificate, args: {args}, env: {env}")

    validate(args, apply_certificate_input_schema)

    res = request_cert_apply({"clientId": env["clientId"], **args})
    if res["code"] != 0:
        raise Exception(res["msg"])

    return [TextContent(type="text", text=f"证书ID：{res['data']['certId']}")]
