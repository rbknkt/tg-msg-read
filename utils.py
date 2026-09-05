# Кэш сообщений в оперативной памяти
message_cache = {}

def get_user_identifier(user) -> str:
    """Возвращает @username, а если его нет — имя пользователя."""
    if not user:
        return "Неизвестный"
    if user.username:
        return f"@{user.username}"
    return user.full_name