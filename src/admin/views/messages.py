from starlette_admin import fields
from tortoise.functions import Count

from src.admin.contrib.tortoise import Admin, ModelView
from src.models.telegram import TelegramMessage


class MessageView(ModelView):
    identity = 'messages'

    label = 'Telegram messages'
    icon = 'fa-solid fa-envelope'

    fields = [
        fields.IntegerField('message_id'),
        fields.DateTimeField('date'),
        fields.StringField('text'),
        fields.StringField('caption'),
        fields.BooleanField('empty'),
        fields.HasOne('from_user', identity='users'),
        fields.HasOne('chat', identity='chats'),
        # fields.HasOne('reply_to_message', identity='messages'),


        # fields.IntegerField('members_count'),
        # fields.StringField('messages_count', exclude_from_create=True, exclude_from_edit=True)

    ]

    exclude_fields_from_list = ['description']

    def get_queryset(self):
        return self.model.all().prefetch_related(
            'chat', 'from_user', 'reply_to_message'
        )


def register(admin: Admin):
    admin.add_view(MessageView(model=TelegramMessage))
