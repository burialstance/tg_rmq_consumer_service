from pathlib import Path

from src.config.settings import settings
from .contrib.tortoise import Admin

from .views import register_admin_views

TEMPLATES = Path(__file__).parent.joinpath('templates')

admin = Admin(
    title=f'{settings.APP_TITLE} v{settings.APP_VERSION}',
    templates_dir=TEMPLATES.as_posix()
)

register_admin_views(admin)
