import asyncio
import json
import logging
import os
from httpx._types import RequestData, RequestFiles, QueryParamTypes
import httpx
from httpx import Timeout
import urllib.parse
from ..common.util import is_path, get_download_path


from .constant import SERVICE_API_BASE

logger = logging.getLogger("service")


class HttpClientManager:
    def __init__(self, timeout: Timeout | None = None):
        self.timeout = timeout or Timeout(
            connect=5,
            read=60,
            write=60,
            pool=5,
        )
        self.client: httpx.Client | None = None

    def __enter__(self):
        self.client = httpx.Client(
            base_url=SERVICE_API_BASE,
            verify=False,
            follow_redirects=True,
            timeout=self.timeout,
        )
        return self.client

    def __exit__(self, exc_type, exc_value, traceback):
        if self.client:
            self.client.close()


def post(
    url: str,
    form_data: dict["data":dict, "files":RequestFiles],
) -> dict:
    logger.info(f"==> post url: {url}, form_data: {form_data}")
    with HttpClientManager() as client:
        data = form_data["data"]
        data = {k: v for k, v in data.items() if v is not None}
        files = form_data.get("files")
        res = request_client_sn(data)
        client_id = data["clientId"]
        del data["clientId"]
        res = client.post(
            f"{url}{'&' if '?' in url else '?'}sn={res['data']['sn']}&clientId={client_id}", data=data, files=files
        ).json()
        logger.info(f"<== url: {url}, res: {res}")
    return res


def get(
    url: str,
    form_data: dict,
):
    logger.info(f"==> get url: {url}, form_data: {form_data}")
    with HttpClientManager() as client:
        form_data = {k: v for k, v in form_data.items() if v is not None}
        res = request_client_sn(form_data)
        form_data["sn"] = res["data"]["sn"]
        res = client.get(url, params=form_data).json()
        logger.info(f"<== url: {url}, res: {res}")
    return res


def request_client_sn(form_data: dict) -> dict:
    if form_data.get("fileUrl"):
        form_data["fileUrl"] = urllib.parse.unquote(form_data["fileUrl"])
    logger.info(f"==> post url: /api/client/sn, form_data: {form_data}")
    with HttpClientManager() as client:
        res = client.post("/api/client/sn", json=form_data).json()
        logger.info(f"<== url: /api/client/sn, res: {res}")
        sn = res["data"].get("sn") if isinstance(res["data"], dict) else None
        if sn is None:
            raise Exception(f"获取sn失败: {json.dumps(res, indent=4, ensure_ascii=False)}")
    return res


def request_file_upload(form_data: dict) -> dict:
    form_data["fileUrl"] = urllib.parse.quote(form_data["fileUrl"], safe='')
    res = post(f"/api/file/upload?fileUrl={form_data['fileUrl']}", {"data": form_data})
    if res["code"] != 0:
        raise Exception(json.dumps(res, indent=4, ensure_ascii=False))
    return res


def save_file(params: dict, env: dict) -> None:
    logger.info(f"save_file params: {params}, env: {env}")
    doc = params["doc"]
    client_id = env["clientId"]
    file_name = urllib.parse.unquote(doc["value"])  # 需要对`%20`等转义字符进行解码，否则下载结果不正确
    res = request_client_sn({"docId": doc["id"], "fileName": file_name, "clientId": client_id})
    url = f"{SERVICE_API_BASE}/api/download?sn={res['data']['sn']}&clientId={client_id}&docId={doc['id']}&fileName={file_name}"

    if env["mode"] == "CLOUD":
        logger.info(f"save_file finish: {url}")
        return url

    path = os.path.join(os.path.dirname(params["path"]) if is_path(params["path"]) else get_download_path(), file_name)
    with HttpClientManager() as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
    logger.info(f"save_file finish: {path}")
    return path


async def request_task(res: dict, params: dict, resultProcessor=None, times: int = 60) -> dict:
    task_id = res["data"]["taskInfo"]["taskId"]
    client_id = params["clientId"]

    percentage = 0
    doc_id = None
    while percentage != 100 or doc_id is None:
        await asyncio.sleep(2)
        if times <= 0:
            raise Exception("Polling result timeout")
        times -= 1

        res = get("/api/task", {"taskId": task_id, "clientId": client_id})
        if res["code"] != 0:
            raise Exception(json.dumps(res, indent=4, ensure_ascii=False))

        data = res.get("data", {})
        if callable(resultProcessor):
            result = resultProcessor(data)
            if result is not None:
                return result
        else:
            percentage = data["taskInfo"].get("percentage")
            doc_id = data["taskInfo"].get("docId")

    logger.info(f"docId: {doc_id}")
    return {"value": "", "id": doc_id, "type": "File", "isExotic": True}


def handle_doc_param(form_data: dict, params: dict, doc_id_key: str = "docId", file_key: str = "inputDocument"):
    path = params["path"]
    client_id = params["clientId"]
    if is_path(path):
        if form_data.get("files") is None:
            form_data["files"] = [(file_key, (os.path.basename(path), open(path, "rb")))]
        else:
            form_data["files"] = [*form_data["files"], (file_key, (os.path.basename(path), open(path, "rb")))]
    else:
        res = request_file_upload({"fileUrl": path, "clientId": client_id})
        form_data["data"][doc_id_key] = res["data"]["docId"]


def request_document_create(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"], "format": params["format"]}}
    handle_doc_param(form_data, params)
    res = post("/api/document/create", form_data)
    return res


def request_document_combine(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"]}}
    if isinstance(params.get("config"), dict) and params["config"]:
        form_data["data"]["config"] = json.dumps(params["config"])
    if isinstance(params.get("path"), list):
        doc_ids = []
        for item in params["path"]:
            res = request_file_upload({"fileUrl": item, "clientId": params["clientId"]})
            doc_ids.append(res["data"]["docId"])
        form_data["data"]["docIds"] = json.dumps(doc_ids)
    else:
        handle_doc_param(form_data, params, "docIds", "inputZipDocument")
    res = post("/api/document/combine", form_data)
    return res


def request_document_compare(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"]}}
    handle_doc_param(
        form_data, {"path": params["basePath"], "clientId": params["clientId"]}, "baseDocId", "inputBaseDocument"
    )
    handle_doc_param(
        form_data,
        {"path": params["comparePath"], "clientId": params["clientId"]},
        "compareDocId",
        "inputCompareDocument",
    )
    form_data["data"]["resultType"] = params["resultType"]
    form_data["data"]["compareType"] = params["compareType"]
    res = post("/api/document/compare", form_data)
    return res


def request_document_compress(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"], "compressionLevel": params.get("compressionLevel")}}
    handle_doc_param(form_data, params)
    res = post("/api/document/compress", form_data)
    return res


def request_document_convert(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"], "format": params["format"]}}
    handle_doc_param(form_data, params)
    if params.get("config"):
        form_data["data"]["config"] = params["config"]
    res = post("/api/document/convert", form_data)
    return res


def request_document_create_from_html(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"], "format": params["format"]}}
    if params["format"] == "url":
        form_data["data"]["url"] = params["url"]
    else:
        handle_doc_param(form_data, params)
    if isinstance(params.get("config"), dict) and params["config"]:
        form_data["data"]["config"] = json.dumps(params["config"])
    else:
        form_data["data"]["config"] = ""
    res = post("/api/document/createFromHtml", form_data)
    return res


def request_document_extract(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"], "mode": params["mode"]}}
    if params.get("pageRange"):
        form_data["data"]["pageRange"] = params["pageRange"]
    handle_doc_param(form_data, params)
    res = post("/api/document/extract", form_data)
    return res


def request_document_flatten(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"], "pageRange": params["pageRange"]}}
    handle_doc_param(form_data, params)
    res = post("/api/document/flatten", form_data)
    return res


def request_document_linearize(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"]}}
    handle_doc_param(form_data, params)
    res = post("/api/document/linearize", form_data)
    return res


def request_document_manipulation(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"]}}
    handle_doc_param(form_data, params)
    if isinstance(params.get("config"), dict) and params["config"]:
        form_data["data"]["config"] = json.dumps([params["config"]])
    else:
        form_data["data"]["config"] = ""
    res = post("/api/document/manipulation", form_data)
    return res


def request_document_protect(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"]}}
    handle_doc_param(form_data, params)
    if isinstance(params.get("passwordProtection"), dict) and params["passwordProtection"]:
        form_data["data"]["passwordProtection"] = json.dumps(params["passwordProtection"])
    else:
        form_data["data"]["passwordProtection"] = ""
    permission = [key for key, value in params["permission"].items() if value]
    form_data["data"]["permission"] = json.dumps(permission)
    form_data["data"]["encryptionAlgorithm"] = params["encryptionAlgorithm"]
    res = post("/api/document/protect", form_data)
    return res


def request_document_remove_password(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"], "password": params["password"]}}
    handle_doc_param(form_data, params)
    res = post("/api/document/removePassword", form_data)
    return res


def request_document_split(params: dict) -> dict:
    form_data = {"data": {"clientId": params["clientId"]}}
    if isinstance(params.get("config"), dict) and params["config"]:
        form_data["data"]["config"] = json.dumps(params["config"])
    else:
        form_data["data"]["config"] = ""
    handle_doc_param(form_data, params)
    res = post("/api/document/split", form_data)
    return res


def request_cert_apply(params: dict) -> dict:
    data = {
        "clientId": params["clientId"],
        "agentName": params.get("agentName"),
        "agentIdCard": params.get("agentIdCard"),
        "agentPhone": params.get("agentPhone"),
        "orgName": params.get("orgName"),
        "orgLegalPerson": params.get("orgLegalPerson"),
        "orgRegisterNo": params.get("orgRegisterNo"),
        "orgLegalPersonIdCard": params.get("orgLegalPersonIdCard"),
    }
    if params.get("certValid") is not None:
        data["certValid"] = params["certValid"]
    form_data = {"data": data}
    res = post("/api/cert/apply", form_data)
    return res


def request_document_sign(params: dict) -> dict:
    data = {
        "clientId": params["clientId"],
        "pageIndex": params.get("pageIndex"),
        "signatureRect": params.get("signatureRect"),
        "certId": params.get("certId"),
    }
    for key in [
        "appearanceFlag",
        "signer",
        "text",
        "location",
        "reason",
        "contactInfo",
    ]:
        value = params.get(key)
        if value is not None:
            data[key] = value

    form_data: dict = {"data": data}
    handle_doc_param(form_data, params)

    if params.get("imagePath"):
        handle_doc_param(
            form_data, {"path": params["imagePath"], "clientId": params["clientId"]}, "imageDocId", "stampImage"
        )

    res = post("/api/document/sign", form_data)
    return res


def request_document_pages_is_scanned(params: dict) -> dict:
    data = {"clientId": params["clientId"]}
    if params.get("pageRange"):
        data["pageRange"] = params["pageRange"]
    form_data: dict = {"data": data}
    handle_doc_param(form_data, params)
    res = post("/api/document/pagesIsScanned", form_data)
    return res


def request_document_pages_basic_info(params: dict) -> dict:
    data = {"clientId": params["clientId"]}
    if params.get("pageRange"):
        data["pageRange"] = params["pageRange"]
    form_data: dict = {"data": data}
    handle_doc_param(form_data, params)
    res = post("/api/document/pagesBasicInfo", form_data)
    return res


def request_document_watermark(params: dict) -> dict:
    data: dict = {"clientId": params["clientId"], "type": params.get("type")}
    if params.get("pageRange"):
        data["pageRange"] = params["pageRange"]
    for key in [
        "position",
        "offsetX",
        "offsetY",
        "flagOnTopOfPage",
        "flagNoPrint",
        "flagInvisible",
        "scaleX",
        "scaleY",
        "rotation",
        "opacity",
    ]:
        val = params.get(key)
        if isinstance(val, (int, float)):
            data[key] = val

    form_data: dict = {"data": data}
    handle_doc_param(form_data, params)

    if params.get("type") == "textObject":
        font = params.get("font", {}) or {}
        font_payload = {
            "text": font.get("text", ""),
        }
        if isinstance(font.get("size"), (int, float)):
            font_payload["size"] = font["size"]
        if font.get("fontName"):
            font_payload["fontName"] = font["fontName"]
        if font.get("color"):
            font_payload["color"] = font["color"]
        if isinstance(font.get("style"), (int, float)):
            font_payload["style"] = font["style"]
        if isinstance(font.get("alignment"), (int, float)):
            font_payload["alignment"] = font["alignment"]
        if isinstance(font.get("lineSpace"), (int, float)):
            font_payload["lineSpace"] = font["lineSpace"]
        form_data["data"]["font"] = json.dumps(font_payload)
    elif params.get("type") == "imageObject":
        if params.get("imagePath"):
            handle_doc_param(
                form_data, {"path": params["imagePath"], "clientId": params["clientId"]}, "imageDocId", "watermarkImage"
            )

    res = post("/api/document/watermark", form_data)
    return res
