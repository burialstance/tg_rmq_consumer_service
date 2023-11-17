from fastapi import FastAPI

from .admin import admin


def register_admin_app(app: FastAPI):
    admin.mount_to(app)
