from starlette_admin import DropDown
from src.admin.contrib.tortoise import Admin

from . import users, chats, messages


def register_admin_views(admin: Admin):
    users.register(admin)
    chats.register(admin)
    messages.register(admin)
