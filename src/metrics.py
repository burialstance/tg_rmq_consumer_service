from prometheus_client import Counter

TELEGRAM_MESSAGES_TOTAL = Counter(
    'telegram_messages_total',
    'Total count of consuming telegram messages ',
    labelnames=('chat_id', 'title',)
)

TELEGRAM_REPLIES_TO_MESSAGE_TOTAL = Counter(
    'telegram_replies_to_message',
    'Count of telegram messages with replies'
)

TELEGRAM_MESSAGES_WITH_CRYPTOBOX = Counter(
    'telegram_messages_with_cryptobox',
    'Count of consuming telegram messages with cryptoboxes',
    labelnames=('chat_id', 'title', )
)

TELEGRAM_RESTRICTED_CHAT_MESSAGES = Counter(
    'telegram_restricted_chat_messages',
    'Consumed messages from restricted chat source',
    labelnames=('chat_id', 'chat_title')
)

TELEGRAM_RESTRICTED_USER_MESSAGES = Counter(
    'telegram_restricted_user_messages',
    'Consumed messages from restricted user source',
    labelnames=('user_id', 'user_username')
)


