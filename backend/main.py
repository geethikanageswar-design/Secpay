from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, init_db
from app.routes import auth, providers, bills, payments, dashboard

# Create tables and log the connection/creation process
init_db()


app = FastAPI(title="SecPay API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": str(exc.detail), "code": exc.status_code}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": "Validation Error", "code": 400}
    )

import traceback
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("GLOBAL EXCEPTION CAUGHT:", exc, flush=True)
    traceback.print_exc()
    # Do not expose internal exception traces to frontend.
    return JSONResponse(
        status_code=500, 
        content={"status": "error", "message": "Internal Server Error", "code": 500}
    )


app.include_router(auth.router)
app.include_router(providers.router)
app.include_router(bills.router)
app.include_router(payments.router)
app.include_router(dashboard.router)

from app.routes import admin
app.include_router(admin.router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "SecPay API is running"}
# Trigger reload
