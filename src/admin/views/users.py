from starlette.requests import Request
from starlette_admin import fields, DropDown
from tortoise.functions import Count

from src.admin.contrib.tortoise import Admin, ModelView
from src.models.telegram import TelegramUser, TelegramUserBlacklist

USERS_ICON = 'fa-solid fa-users'


class UserView(ModelView):
    model = TelegramUser
    identity = 'users'
    label = 'Telegram users'
    icon = USERS_ICON

    fields = [
        fields.IntegerField('id'),
        fields.BooleanField('is_bot'),
        fields.StringField('username'),
        fields.StringField('first_name'),
        fields.StringField('last_name'),
        fields.StringField('full_name', exclude_from_create=True, exclude_from_edit=True),
        fields.StringField('bio'),
        fields.IntegerField(
            'messages_count',
            label='messages',
            exclude_from_create=True,
            exclude_from_edit=True
        ),
        # fields.IntegerField(
        #     'violations_count',
        #     label='violations',
        #     exclude_from_create=True,
        #     exclude_from_edit=True
        # ),
    ]

    exclude_fields_from_list = [
        'first_name',
        'last_name',
    ]

    def get_queryset(self):
        return self.model.all().annotate(
            messages_count=Count('messages'),
            # violations_count=Count('blacklist')
        )

    async def repr(self, obj: TelegramUser, request: Request) -> str:
        return obj.username or obj.full_name or obj.id


class HistoryBlacklistUserView(ModelView):
    model = TelegramUserBlacklist

    identity = 'users_blacklist_history'
    label = 'Blacklist history'

    fields = [
        fields.IntegerField('id'),
        fields.HasOne('user', identity='users'),
        fields.StringField('reason'),
        fields.DateTimeField('release_at'),
        fields.StringField('release_at_humanize'),

        fields.StringField('amnestied_reason'),
        fields.DateTimeField('amnestied_at'),
        fields.StringField('amnestied_at_humanize'),
    ]

    exclude_fields_from_create = [
        'release_at_humanize',

        'amnestied_reason',
        'amnestied_at',
        'amnestied_at_humanize'
    ]

    exclude_fields_from_edit = [
        'release_at_humanize',
        'amnestied_at_humanize'
    ]
    exclude_fields_from_list = [
        'id', 'release_at', 'amnestied_at'
    ]

    def get_queryset(self):
        qs = self.model.all()
        return qs.prefetch_related('user')


class ActiveBlacklistUserView(HistoryBlacklistUserView):
    identity = 'users_blacklist_active'
    label = 'Blacklist active'

    def get_queryset(self):
        qs = self.model.objects.get_queryset().restricted()
        return qs.prefetch_related('user')


def register(admin: Admin):
    admin.add_view(DropDown(label='Telegram users', icon=USERS_ICON, views=[
        UserView(label='Entities'),
        HistoryBlacklistUserView(label='Blacklist History'),
        ActiveBlacklistUserView(label='Blacklist Active')
    ]))
