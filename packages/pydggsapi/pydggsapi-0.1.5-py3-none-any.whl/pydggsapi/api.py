# Test for sub-folder changes
from fastapi import FastAPI, Depends, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv

import pydggsapi.request_example as request_example
from pydggsapi.routers import dggs_api
from pydggsapi.routers import tiles_api

import os
import json
import logging
import importlib.metadata

version = importlib.metadata.version('pydggsapi')

logger = logging.getLogger()
load_dotenv()
logger.debug("Environment configuration:\n%s", json.dumps(dict(os.environ), indent=2))
api_title = os.environ.get('API_TITLE', 'University of Tartu, OGC DGGS API v1-pre')
api_description = os.environ.get('API_DESCRIPTION', 'OGC DGGS API')
api_contact = json.loads(os.environ.get('API_CONTACT') or '{}') or {
    "name": "Contact project lead",
    "url": "https://landscape-geoinformatics.ut.ee/expertise/dggs/",
    "email": "alexander.kmoch@ut.ee"
}
root_path = os.environ.get('ROOT_PATH')
openapi_url = os.environ.get('OPENAPI_URL', '/openapi.json')
docs_url = os.environ.get("DOCS_URL", "/docs")
redoc_url = os.environ.get("REDOC_URL", "/redoc")
swagger_ui_oauth2_redirect_url = os.environ.get("SWAGGER_UI_OAUTH2_REDIRECT_URL", "/docs/oauth2-redirect")
app = FastAPI(
    title=api_title,
    description=api_description,
    version=version,
    root_path=root_path,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    swagger_ui_oauth2_redirect_url=swagger_ui_oauth2_redirect_url,
)
# initialize logging for Fastapi

# Setting up CORS
origins = os.environ.get('CORS', [])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dggs_prefix = os.environ.get('DGGS_PREFIX', '/dggs-api/v1-pre')
tiles_prefix = os.environ.get('TILES_PREFIX', '/tiles-api')

app.include_router(dggs_api.router, prefix=dggs_prefix)
app.include_router(tiles_api.router, prefix=tiles_prefix)



# set up a landing page GET /

######################################################
# openapi
# https://swagger.io/docs/specification/describing-parameters/#header-parameters
# https://www.linode.com/docs/guides/documenting-a-fastapi-app-with-openapi/
######################################################

def my_schema():
    openapi_schema = get_openapi(
        title="pydggsapi: A python FastAPI OGC DGGS API implementation",
        version="0.1.5",
        routes=app.routes,
        servers=[{"url": root_path}] if root_path else None,
    )

    openapi_schema["info"] = {
        "title" : "pydggsapi: A python FastAPI OGC DGGS API implementation",
        "version" : "0.1.5",
        "description" : "A python FastAPI OGC DGGS API implementation",
        "termsOfService": "https://creativecommons.org/licenses/by/4.0/",
        "contact": api_contact,
        "license": {
            "name": "AGPL-3.0",
            "url": "https://www.gnu.org/licenses/agpl-3.0.en.html"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = my_schema
