import os
import sys
from fastapi import FastAPI


fastapi_app = FastAPI(port=os.environ.get('PORT', 8080),
                      docs_url='/api/docs')
