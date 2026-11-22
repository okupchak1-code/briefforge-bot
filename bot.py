import asyncio
import os
from dataclasses import dataclass, field

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не знайдено BOT_TOKEN у файлі .env")

PROJECT_TYPES = {
    "site": {
        "uk": "Сайт / Лендінг",
        "en": "Website / Landing",
        "base_days": 5,
        "base_points": 2,
    },
    "bot": {
        "uk": "Telegram-бот",
        "en": "Telegram Bot",
        "base_days": 7,
        "base_points": 3,
    },
    "webapp": {
        "uk": "Веб-сервіс / MVP",
        "en": "Web App / MVP",
        "base_days": 14,
        "base_points": 5,
    },
}

COMPLEXITIES = {
    "basic": {
        "uk": "Базовий (MVP)",
        "en": "Basic (MVP)",
        "mult": 1.0,
        "points": 1,
        "label_uk": "Низька",
        "label_en": "Low",
    },
    "standard": {
        "uk": "Стандартний",
        "en": "Standard",
        "mult": 1.4,
        "points": 3,
        "label_uk": "Середня",
        "label_en": "Medium",
    },
    "custom": {
        "uk": "Складний / Кастом",
        "en": "Complex / Custom",
        "mult": 2.0,
        "points": 6,
        "label_uk": "Висока",
        "label_en": "High",
    },
}

FEATURES = {
    "auth": {"uk": "Авторизація / Ролі", "en": "Auth & Roles", "days": 2, "points": 2},
    "payments": {"uk": "Прийом оплат", "en": "Payments", "days": 3, "points": 3},
    "admin": {"uk": "Адмін-панель", "en": "Admin Panel", "days": 4, "points": 3},
    "api_db": {"uk": "БД та зовнішнє API", "en": "DB & External API", "days": 3, "points": 2},
    "i18n": {"uk": "Мультимовність", "en": "Multi-language", "days": 2, "points": 1},
}

TEXTS = {
    "uk": {
        "welcome": (
            "<b>BriefForge Bot</b> — інтерактивний конструктор ТЗ та оцінки проєкту.\n\n"
            "Крок 1/3: обери <b>тип проєкту</b>:"
        ),
        "step_complexity": (
            "Тип: <b>{project_type}</b>\n\n"
            "Крок 2/3: обери <b>рівень реалізації</b>:"
        ),
        "step_features": (
            "Тип: <b>{project_type}</b>\n"
            "Рівень: <b>{complexity}</b>\n\n"
            "Крок 3/3: відміть потрібні <b>модулі</b> (можна обрати кілька) і натисни «Сформувати ТЗ»:"
        ),
        "btn_lang": "🌐 English",
        "btn_back_type": "⬅️ Змінити тип",
        "btn_back_comp": "⬅️ Змінити рівень",
        "btn_build": "📄 Сформувати ТЗ",
        "btn_restart": "🔄 Новий бриф",
        "none_features": "Базовий набір без додаткових модулів",
        "spec_title": "<b>📋 ГОТОВЕ ТЕХНІЧНЕ ЗАВДАННЯ (BRIEF)</b>",
        "lbl_type": "Напрямок",
        "lbl_comp": "Рівень",
        "lbl_features": "Модулі",
        "lbl_score": "Індекс складності",
        "lbl_est": "Орієнтовний термін",
        "days_unit": "дн.",
        "lang_switched": "Мову змінено на українську.",
    },
    "en": {
        "welcome": (
            "<b>BriefForge Bot</b> — interactive tech-spec & scope estimator.\n\n"
            "Step 1/3: choose a <b>project type</b>:"
        ),
        "step_complexity": (
            "Type: <b>{project_type}</b>\n\n"
            "Step 2/3: choose a <b>complexity tier</b>:"
        ),
        "step_features": (
            "Type: <b>{project_type}</b>\n"
            "Tier: <b>{complexity}</b>\n\n"
            "Step 3/3: toggle required <b>modules</b> (multiple allowed) and tap «Generate Spec»:"
        ),
        "btn_lang": "🌐 Українська",
        "btn_back_type": "⬅️ Change Type",
        "btn_back_comp": "⬅️ Change Tier",
        "btn_build": "📄 Generate Spec",
        "btn_restart": "🔄 New Brief",
        "none_features": "Core scope without extra modules",
        "spec_title": "<b>📋 GENERATED TECHNICAL BRIEF</b>",
        "lbl_type": "Category",
        "lbl_comp": "Tier",
        "lbl_features": "Modules",
        "lbl_score": "Complexity Index",
        "lbl_est": "Estimated Timeline",
        "days_unit": "days",
        "lang_switched": "Switched language to English.",
    },
}


@dataclass
class BriefSession:
    lang: str = "en"
    step: str = "type"  # type | complexity | features | result
    project_type: str | None = None
    complexity: str | None = None
    features: set[str] = field(default_factory=set)


sessions: dict[int, BriefSession] = {}


def detect_lang(code: str | None) -> str:
    return "uk" if code and code.lower().startswith("uk") else "en"


def get_session(user_id: int, tg_lang: str | None) -> BriefSession:
    if user_id not in sessions:
        sessions[user_id] = BriefSession(lang=detect_lang(tg_lang))
    return sessions[user_id]


def kb_type(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    rows = [
        [
            InlineKeyboardButton(
                text=PROJECT_TYPES[key][lang],
                callback_data=f"set_type:{key}",
            )
        ]
        for key in PROJECT_TYPES
    ]
    rows.append([InlineKeyboardButton(text=t["btn_lang"], callback_data="toggle_lang")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_complexity(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    rows = [
        [
            InlineKeyboardButton(
                text=COMPLEXITIES[key][lang],
                callback_data=f"set_comp:{key}",
            )
        ]
        for key in COMPLEXITIES
    ]
    rows.append(
        [
            InlineKeyboardButton(text=t["btn_back_type"], callback_data="back:type"),
            InlineKeyboardButton(text=t["btn_lang"], callback_data="toggle_lang"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_features(lang: str, selected: set[str]) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    rows: list[list[InlineKeyboardButton]] = []
    for key, meta in FEATURES.items():
        mark = "✅" if key in selected else "⬜"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {meta[lang]}",
                    callback_data=f"toggle_feat:{key}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t["btn_build"], callback_data="build_spec")])
    rows.append(
        [
            InlineKeyboardButton(text=t["btn_back_comp"], callback_data="back:complexity"),
            InlineKeyboardButton(text=t["btn_lang"], callback_data="toggle_lang"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_result(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t["btn_restart"], callback_data="restart")],
            [InlineKeyboardButton(text=t["btn_lang"], callback_data="toggle_lang")],
        ]
    )


def render_spec(session: BriefSession) -> str:
    lang = session.lang
    t = TEXTS[lang]
    ptype_key = session.project_type or "bot"
    comp_key = session.complexity or "basic"

    ptype_meta = PROJECT_TYPES[ptype_key]
    comp_meta = COMPLEXITIES[comp_key]

    feat_names = [FEATURES[f][lang] for f in FEATURES if f in session.features]
    feat_days = sum(FEATURES[f]["days"] for f in session.features if f in FEATURES)
    feat_points = sum(FEATURES[f]["points"] for f in session.features if f in FEATURES)

    total_days = max(2, round((ptype_meta["base_days"] + feat_days) * comp_meta["mult"]))
    total_points = ptype_meta["base_points"] + comp_meta["points"] + feat_points
    tier_label = comp_meta["label_uk"] if lang == "uk" else comp_meta["label_en"]
    features_text = ", ".join(feat_names) if feat_names else t["none_features"]

    return (
        f"{t['spec_title']}\n\n"
        f"• <b>{t['lbl_type']}:</b> {ptype_meta[lang]}\n"
        f"• <b>{t['lbl_comp']}:</b> {comp_meta[lang]}\n"
        f"• <b>{t['lbl_features']}:</b> {features_text}\n"
        f"• <b>{t['lbl_score']}:</b> {total_points} pts ({tier_label})\n"
        f"• <b>{t['lbl_est']}:</b> ~{total_days} {t['days_unit']}"
    )


async def render_current_view(callback: CallbackQuery, session: BriefSession) -> None:
    lang = session.lang
    t = TEXTS[lang]

    if session.step == "type":
        await callback.message.edit_text(
            t["welcome"], reply_markup=kb_type(lang), parse_mode="HTML"
        )
    elif session.step == "complexity":
        ptype_name = PROJECT_TYPES[session.project_type or "bot"][lang]
        await callback.message.edit_text(
            t["step_complexity"].format(project_type=ptype_name),
            reply_markup=kb_complexity(lang),
            parse_mode="HTML",
        )
    elif session.step == "features":
        ptype_name = PROJECT_TYPES[session.project_type or "bot"][lang]
        comp_name = COMPLEXITIES[session.complexity or "basic"][lang]
        await callback.message.edit_text(
            t["step_features"].format(project_type=ptype_name, complexity=comp_name),
            reply_markup=kb_features(lang, session.features),
            parse_mode="HTML",
        )
    elif session.step == "result":
        await callback.message.edit_text(
            render_spec(session), reply_markup=kb_result(lang), parse_mode="HTML"
        )


async def cmd_start(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0
    tg_lang = message.from_user.language_code if message.from_user else None
    session = BriefSession(lang=detect_lang(tg_lang), step="type")
    sessions[user_id] = session
    await message.answer(
        TEXTS[session.lang]["welcome"],
        reply_markup=kb_type(session.lang),
        parse_mode="HTML",
    )


async def on_set_type(callback: CallbackQuery) -> None:
    session = get_session(callback.from_user.id, callback.from_user.language_code)
    session.project_type = (callback.data or "").split(":", maxsplit=1)[-1]
    session.step = "complexity"
    await render_current_view(callback, session)
    await callback.answer()


async def on_set_comp(callback: CallbackQuery) -> None:
    session = get_session(callback.from_user.id, callback.from_user.language_code)
    session.complexity = (callback.data or "").split(":", maxsplit=1)[-1]
    session.step = "features"
    await render_current_view(callback, session)
    await callback.answer()


async def on_toggle_feat(callback: CallbackQuery) -> None:
    session = get_session(callback.from_user.id, callback.from_user.language_code)
    feat = (callback.data or "").split(":", maxsplit=1)[-1]
    if feat in session.features:
        session.features.remove(feat)
    else:
        session.features.add(feat)
    await render_current_view(callback, session)
    await callback.answer()


async def on_build_spec(callback: CallbackQuery) -> None:
    session = get_session(callback.from_user.id, callback.from_user.language_code)
    session.step = "result"
    await render_current_view(callback, session)
    await callback.answer()


async def on_back(callback: CallbackQuery) -> None:
    session = get_session(callback.from_user.id, callback.from_user.language_code)
    target = (callback.data or "").split(":", maxsplit=1)[-1]
    session.step = target
    await render_current_view(callback, session)
    await callback.answer()


async def on_restart(callback: CallbackQuery) -> None:
    lang = get_session(callback.from_user.id, callback.from_user.language_code).lang
    sessions[callback.from_user.id] = BriefSession(lang=lang, step="type")
    await render_current_view(callback, sessions[callback.from_user.id])
    await callback.answer()


async def on_toggle_lang(callback: CallbackQuery) -> None:
    session = get_session(callback.from_user.id, callback.from_user.language_code)
    session.lang = "en" if session.lang == "uk" else "uk"
    await render_current_view(callback, session)
    await callback.answer(TEXTS[session.lang]["lang_switched"])


async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(cmd_start, CommandStart())
    dp.callback_query.register(on_set_type, F.data.startswith("set_type:"))
    dp.callback_query.register(on_set_comp, F.data.startswith("set_comp:"))
    dp.callback_query.register(on_toggle_feat, F.data.startswith("toggle_feat:"))
    dp.callback_query.register(on_build_spec, F.data == "build_spec")
    dp.callback_query.register(on_back, F.data.startswith("back:"))
    dp.callback_query.register(on_restart, F.data == "restart")
    dp.callback_query.register(on_toggle_lang, F.data == "toggle_lang")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())