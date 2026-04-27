"""Mongolian copy: /start sections, rules, and /help."""

from utils.constants import REWARD_THRESHOLDS


def _reward_lines() -> str:
    ordered = sorted(REWARD_THRESHOLDS.items(), key=lambda x: x[0])
    return "\n".join(f"• {count:,} invite — {amount}" for count, amount in ordered)


def help_full_text() -> str:
    return (
        "🧭 <b>Тусламж</b>\n\n"
        "Private chat:\n"
        "• <code>/start</code> — bot идэвхжүүлэх\n"
        "• <code>/profile @username</code> — profile харах\n"
        "• <code>/good @username</code> — good үнэлгээ өгөх\n"
        "• <code>/bad @username</code> — bad үнэлгээ өгөх\n"
        "• <code>/report @username</code> — report эхлүүлэх\n"
        "• <code>/invite</code> — урилгын линк авах\n\n"
        "Group:\n"
        "• <code>/menu</code> — үндсэн цэс нээх\n"
        "• Хүний мессеж дээр reply хийгээд: 👍 Good / 👎 Bad / 👤 Profile / ⚠️ Report\n\n"
        "📌 Rating limit: нэг хэрэглэгч 72 цагт нийт 2 good/bad өгч чадна\n"
        "↩️ Undo: өгсөн үнэлгээг 10 секундэд буцаах боломжтой"
    )


def section_rules_and_trust() -> str:
    return (
        "📘 <b>Дүрэм & Trust</b>\n\n"
        "🛡 Community цэвэр, ойлгомжтой, найдвартай байх нь хамгийн чухал.\n\n"
        "1) Үндсэн дүрэм\n"
        "• Хүндэтгэлтэй харилцана\n"
        "• Луйвар, spam, fake account, олон account-аар system abuse хийхийг хориглоно\n"
        "• Худал мэдээлэл, бусдыг төөрөгдүүлэх оролдлого хийхгүй\n"
        "• Системийг зориуд exploit хийх оролдлого count болохгүй\n\n"
        "2) Trust оноо хэрхэн өсөх вэ?\n"
        "• 👍 Good авах тусам Trust оноо өснө\n"
        "• 👎 Bad авбал Trust оноо буурна\n"
        "• Бодит урилга, зөв оролцоо, эерэг нэр хүнд badge өсөхөд нөлөөлнө\n"
        "• Approved report ихэсвэл нэр хүнд буурна\n\n"
        "3) Trust оноо\n"
        "• Формул: <code>max(0, good - bad)</code>\n"
        "• 0-ээс эхэлнэ\n"
        "• Дээд хязгааргүй\n"
        "• Badge нь босго даваад автоматаар өснө\n\n"
        "4) Badge шатлал\n"
        "• 0–9 — Шинэ гишүүн\n"
        "• 10–49 — Идэвхтэй гишүүн\n"
        "• 50–199 — Итгэлтэй гишүүн\n"
        "• 200+ — Verified\n\n"
        "5) Хэрхэн хурдан өсгөх вэ?\n"
        "• Тогтвортой, соёлтой идэвхтэй байх\n"
        "• Бодит гишүүд урьж оруулах\n"
        "• Spam, scam, abuse-аас хол байх"
    )


def section_invite_growth() -> str:
    return (
        "📨 <b>Invite систем</b>\n\n"
        "🔗 Урилгын үзүүлэлт зөвхөн бодитоор group-д нэгдсэн хэрэглэгч дээр өснө.\n\n"
        "• Хуурамч account, spam invite, өөрөө олон account оруулах нь тооцогдохгүй\n"
        "• Урилгын тоо таны profile дээр харагдана\n"
        "• <code>/invite</code> гэж бичин өөрийн link ээ авах боломжтой\n"
        "• Систем зөвхөн real growth-ийг тооцно"
    )


def section_reward_system() -> str:
    return (
        "🎁 <b>Шагнал</b>\n\n"
        "🏆 Шагналын систем бодит урилга болон зөв оролцооны үзүүлэлтээр тооцогдоно.\n\n"
        "<b>Reward tiers:</b>\n"
        f"{_reward_lines()}\n\n"
        "⚠️ Fake invite, spam growth, abuse оролцохгүй.\n"
        "📌 Таны явц profile дээр харагдана."
    )


def section_commands() -> str:
    return (
        "🧭 <b>Командууд</b>\n\n"
        "Private chat:\n"
        "• <code>/start</code> — bot идэвхжүүлэх\n"
        "• <code>/profile @username</code> — profile харах\n"
        "• <code>/good @username</code> — good үнэлгээ өгөх\n"
        "• <code>/bad @username</code> — bad үнэлгээ өгөх\n"
        "• <code>/report @username</code> — report эхлүүлэх\n"
        "• <code>/invite</code> — урилгын линк авах\n\n"
        "Group:\n"
        "• <code>/menu</code> — үндсэн цэс нээх\n"
        "• Хүний мессеж дээр reply хийгээд:\n"
        "  👍 Good\n"
        "  👎 Bad\n"
        "  👤 Profile\n"
        "  ⚠️ Report\n\n"
        "📌 Rating limit: нэг хэрэглэгч 72 цагт нийт 2 good/bad өгч чадна\n"
        "↩️ Undo: өгсөн үнэлгээг 10 секундэд буцаах боломжтой"
    )
