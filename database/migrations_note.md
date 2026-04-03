# Migration Note

Одоогийн хувилбар эхний production schema-г `Base.metadata.create_all()` ашиглан үүсгэнэ.

Production орчинд дараах дарааллыг зөвлөж байна:

1. Alembic нэмэх
2. `alembic revision --autogenerate -m "init schema"` үүсгэх
3. Railway дээр deploy хийхийн өмнө `alembic upgrade head` ажиллуулах

Хэрэв хуучин schema-аас шилжиж байгаа бол:
- `users` хүснэгтэд нэмэгдсэн талбарууд (`is_verified_manual`, `is_verified_auto`, `reward_*`, `has_joined_group`, `is_suspicious`, `warning_count`, `is_banned`, `is_muted_until`) nullable/default тохиргоотой нэм.
- `ratings`, `invites`, `reports`, `moderation_logs`, `spam_logs` индексүүдийг үүсгэ.
