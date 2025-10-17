import os

ENV_BASE = os.getenv("_ENV_BASE", "prod")  # devcn / stgcn / prod

SERVICE_API_BASE = "https://servicesapi-devcn.connectedpdf.com"

if ENV_BASE == "devcn":
    SERVICE_API_BASE = "https://servicesapi-devcn.connectedpdf.com"
elif ENV_BASE == "stgcn":
    SERVICE_API_BASE = "https://servicesapi-stgcn.connectedpdf.com"
elif ENV_BASE == "prod":
    SERVICE_API_BASE = "https://servicesapi.foxitsoftware.cn"
