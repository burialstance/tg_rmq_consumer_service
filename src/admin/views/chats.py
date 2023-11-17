from typing import List

from starlette.datastructures import FormData
from starlette.requests import Request
from starlette_admin import fields, DropDown, action
from tortoise.functions import Count

from src.admin.contrib.tortoise import Admin, ModelView
from src.models.telegram import TelegramChat, TelegramChatBlacklist

CHAT_ICON = 'fa-solid fa-comment-dots'

ADD_TO_BLACKLIST_FORM = """
<form>
    <div class="mt-3">
        <input type="text" class="form-control" name="reason" placeholder="Reason">
        
        <!-- <input type="radio" class="btn-check" name="btn-radio-basic" id="btn-radio-basic-1" autocomplete="off" checked=""> -->
        <!-- <label for="btn-radio-basic-1" type="button" class="btn">1H</label> -->

        <!-- <input type="radio" class="btn-check" name="btn-radio-basic" id="btn-radio-basic-2" autocomplete="off"> -->
        <!-- <label for="btn-radio-basic-2" type="button" class="btn">4H</label> -->

        <!-- <input type="radio" class="btn-check" name="btn-radio-basic" id="btn-radio-basic-3" autocomplete="off"> -->
        <!-- <label for="btn-radio-basic-3" type="button" class="btn">1D</label> -->

        <!-- <input type="radio" class="btn-check" name="btn-radio-basic" id="btn-radio-basic-4" autocomplete="off"> -->
        <!-- <label for="btn-radio-basic-4" type="button" class="btn">7D</label> -->

        <!-- <input type="radio" class="btn-check btn-outline-danger" name="btn-radio-basic" id="btn-radio-basic-5" autocomplete="off"> -->
        <!-- <label for="btn-radio-basic-5" type="button" class="btn">PERM</label> -->
    </div>
</form>
"""


class ChatView(ModelView):
    model = TelegramChat
    identity = 'chats'

    label = 'Telegram chats'
    icon = CHAT_ICON

    fields = [
        fields.IntegerField('id'),
        fields.EnumField('type', enum=TelegramChat.ChatType),
        fields.StringField('title'),
        fields.StringField('username'),
        fields.StringField('description'),
        fields.IntegerField('members_count'),
        fields.IntegerField('messages_count', exclude_from_create=True, exclude_from_edit=True)

    ]

    exclude_fields_from_list = ['description']

    actions = [
        'delete',
        'add_to_blacklist'
    ]

    def get_queryset(self):
        return self.model.all().annotate(
            messages_count=Count('messages'),
        )

    async def repr(self, obj: TelegramChat, request: Request) -> str:
        return obj.title

    @action(
        name='add_to_blacklist',
        confirmation='Are you sure?',
        text='Add to blacklist',
        form=ADD_TO_BLACKLIST_FORM
    )
    async def add_to_blacklist(self, request: Request, pks: List[int]):
        data: FormData = await request.form()
        return str(data)


class HistoryBlacklistChatView(ModelView):
    model = TelegramChatBlacklist

    identity = 'chats_blacklist_history'
    label = 'Blacklist history'

    fields = [
        fields.IntegerField('id'),
        fields.HasOne('chat', identity='chats'),
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
        return qs.prefetch_related('chat')


class ActiveBlacklistChatView(HistoryBlacklistChatView):
    identity = 'chats_blacklist_active'
    label = 'Blacklist active'

    def get_queryset(self):
        qs = self.model.objects.get_queryset().restricted()
        return qs.prefetch_related('chat')


def register(admin: Admin):
    admin.add_view(DropDown('Telegram chats', icon=CHAT_ICON, views=[
        ChatView(label='Entities'),
        HistoryBlacklistChatView(label='Blacklist history'),
        ActiveBlacklistChatView(label='Blacklist active')
    ]))
