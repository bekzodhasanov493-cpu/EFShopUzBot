import asyncio
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)


# =========================================================
# SOZLAMALAR
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylda topilmadi!")

CHANNEL_USERNAME = "@EFShop_UZ"
CHANNEL_LINK = "https://t.me/EFShop_UZ"

# =========================================================
# TO'LOV SOZLAMALARI
# =========================================================

ADMIN_ID = 6595240938

CARD_NUMBER = "9860 1766 2112 4625"
CARD_OWNER = "BEKZOD XASANOV"


# =========================================================
# BOT VA DISPATCHER
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()


# =========================================================
# ADMIN TASDIG'INI KUTAYOTGAN E'LONLAR
# =========================================================

pending_ads = {}


# =========================================================
# FSM HOLATLARI
# =========================================================

class AdForm(StatesGroup):

    # Sotish e'loni
    selling_photo = State()
    google_gamecenter = State()
    exchange = State()
    selling_type = State()
    selling_price = State()
    selling_comment = State()

    # To'lov
    payment_waiting = State()
    payment_submitted = State()

    # Olish e'loni
    buying = State()


# =========================================================
# ASOSIY MENYU
# =========================================================

def main_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🔎 Akkaunt qidirish"
                )
            ],
            [
                KeyboardButton(
                    text="➕ E'lon berish"
                ),
                KeyboardButton(
                    text="📂 E'lonlarim"
                )
            ],
            [
                KeyboardButton(
                    text="🛡 Adminlar"
                ),
                KeyboardButton(
                    text="📚 Qoidalar"
                )
            ],
            [
                KeyboardButton(
                    text="💰 E'lon narxlari"
                )
            ],
        ],
        resize_keyboard=True
    )


# =========================================================
# ORQAGA TUGMASI
# =========================================================

def back_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🔙 Orqaga"
                )
            ]
        ],
        resize_keyboard=True
    )


# =========================================================
# XIZMAT NARXINI HISOBLASH
# =========================================================

def get_service_price(
    selling_type,
    price
):

    # Faqat obmen
    if selling_type == "faqat_obmen":
        return 5000

    if not price:
        return 5000

    try:

        clean_price = (
            str(price)
            .replace("so'm", "")
            .replace("so‘m", "")
            .replace(".", "")
            .replace(",", "")
            .replace(" ", "")
            .strip()
        )

        account_price = int(clean_price)

    except (ValueError, TypeError):

        return 5000

    if account_price <= 500000:

        return 5000

    elif account_price <= 1500000:

        return 7000

    else:

        return 10000


# =========================================================
# OBUNA TEKSHIRISH
# =========================================================

async def check_subscription(
    user_id: int
) -> bool:

    try:

        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )

        return member.status in {
            "member",
            "administrator",
            "creator"
        }

    except Exception:

        return False


# =========================================================
# OBUNA OYNASI
# =========================================================

def subscription_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="EF SHOP UZ 🛍️",
                    url=CHANNEL_LINK
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Davom etish",
                    callback_data="continue_check"
                )
            ]
        ]
    )


# =========================================================
# /START
# =========================================================

@dp.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "👋 <b>EF SHOP UZ</b> ga xush kelibsiz!\n\n"
            "Botdan foydalanish uchun avval "
            "kanalimizga obuna bo‘ling 👇",
            reply_markup=subscription_keyboard()
        )

        return

    await message.answer(
        "👋 <b>EF SHOP UZ</b> ga xush kelibsiz!\n\n"
        "Kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu()
    )


# =========================================================
# DAVOM ETISH
# =========================================================

@dp.callback_query(
    F.data == "continue_check"
)
async def continue_check(
    callback: CallbackQuery
):

    subscribed = await check_subscription(
        callback.from_user.id
    )

    if not subscribed:

        await callback.answer(
            "❌ Avval kanalga obuna bo‘ling!",
            show_alert=True
        )

        return

    await callback.message.delete()

    await callback.message.answer(
        "✅ <b>Obuna tasdiqlandi!</b>\n\n"
        "Kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu()
    )

    await callback.answer()


# =========================================================
# E'LON BERISH
# =========================================================

@dp.message(
    F.text == "➕ E'lon berish"
)
async def add_ad(
    message: Message,
    state: FSMContext
):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Botdan foydalanish uchun "
            "kanalimizga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    await state.clear()

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🔺 Sotish e'loni"
                )
            ],
            [
                KeyboardButton(
                    text="🔻 Olish e'loni"
                )
            ],
            [
                KeyboardButton(
                    text="🔙 Orqaga"
                )
            ],
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📢 <b>E'lon turini tanlang:</b>",
        reply_markup=keyboard
    )


# =========================================================
# SOTISH E'LONI
# =========================================================

@dp.message(
    F.text == "🔺 Sotish e'loni"
)
async def sell_ad(
    message: Message,
    state: FSMContext
):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Botdan foydalanish uchun "
            "kanalimizga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    await state.clear()

    await state.set_state(
        AdForm.selling_photo
    )

    await message.answer(
        "⏳ <b>E'lon berish boshlanmoqda...</b>",
        reply_markup=ReplyKeyboardRemove()
    )

    try:

        photo = FSInputFile(
            "sample.png.jpg"
        )

        await message.answer_photo(
            photo=photo,
            caption="🖼 <b>Namuna</b>"
        )

    except FileNotFoundError:

        await message.answer(
            "⚠️ <b>Namuna rasmi topilmadi.</b>\n\n"
            "Bot papkasida "
            "<code>sample.png.jpg</code> "
            "fayli bo‘lishi kerak."
        )

    await message.answer(
        "📸 <b>O‘z akkauntingiz rasmini "
        "namunadagidek yuboring.</b>"
    )


# =========================================================
# AKKAUNT RASMINI QABUL QILISH
# =========================================================

@dp.message(
    AdForm.selling_photo,
    F.photo
)
async def receive_selling_photo(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        account_photo=message.photo[-1].file_id
    )

    await state.set_state(
        AdForm.google_gamecenter
    )

    google_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅"),
                KeyboardButton(text="❌")
            ],
            [
                KeyboardButton(
                    text="Bekor qilish"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🔐 <b>Qabul qilindi, akkauntingizga "
        "Google yoki Game Center ulanganmi?</b>",
        reply_markup=google_keyboard
    )


# =========================================================
# GOOGLE / GAME CENTER JAVOBI
# =========================================================

@dp.message(
    AdForm.google_gamecenter,
    F.text.in_({"✅", "❌"})
)
async def google_gamecenter_answer(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        google_gamecenter=message.text
    )

    await state.set_state(
        AdForm.exchange
    )

    exchange_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="✅"),
                KeyboardButton(text="❌")
            ],
            [
                KeyboardButton(
                    text="Bekor qilish"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🟢 <b>Qabul qilindi, ushbu akkauntingizga "
        "obmen ko‘rasizmi?</b>",
        reply_markup=exchange_keyboard
    )


# =========================================================
# OBMEN JAVOBI
# =========================================================

@dp.message(
    AdForm.exchange,
    F.text.in_({"✅", "❌"})
)
async def exchange_answer(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        exchange=message.text
    )

    await state.set_state(
        AdForm.selling_type
    )

    sale_type_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📝 Narxni kiritish"
                ),
                KeyboardButton(
                    text="♻️ Faqat obmen"
                )
            ],
            [
                KeyboardButton(
                    text="Bekor qilish"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📋 <b>Akkauntingiz sotiladimi "
        "yoki obmen uchunmi?</b>",
        reply_markup=sale_type_keyboard
    )


# =========================================================
# NARXNI KIRITISH
# =========================================================

@dp.message(
    AdForm.selling_type,
    F.text == "📝 Narxni kiritish"
)
async def ask_price(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        selling_type="sotish"
    )

    await state.set_state(
        AdForm.selling_price
    )

    price_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Bekor qilish"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "💵 <b>Qabul qilindi, ushbu akkount "
        "narxini yuboring:</b>\n\n"
        "<b>Masalan:</b> 250.000",
        reply_markup=price_keyboard
    )


# =========================================================
# FAQAT OBMEN
# =========================================================

@dp.message(
    AdForm.selling_type,
    F.text == "♻️ Faqat obmen"
)
async def only_exchange(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        selling_type="faqat_obmen",
        price=None
    )

    await state.set_state(
        AdForm.selling_comment
    )

    await message.answer(
        "📝 <b>Akkountga qo‘shimcha "
        "izoh yozishingiz mumkin</b>",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# NARXNI QABUL QILISH
# =========================================================

@dp.message(
    AdForm.selling_price,
    F.text
)
async def receive_price(
    message: Message,
    state: FSMContext
):

    if message.text == "Bekor qilish":

        await state.clear()

        await message.answer(
            "🏠 <b>Asosiy menyuga qaytdingiz.</b>\n\n"
            "Kerakli bo‘limni tanlang 👇",
            reply_markup=main_menu()
        )

        return

    price = message.text.strip()

    await state.update_data(
        price=price
    )

    await state.set_state(
        AdForm.selling_comment
    )

    await message.answer(
        "📝 <b>Akkountga qo‘shimcha "
        "izoh yozishingiz mumkin</b>",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# QO'SHIMCHA IZOHLARNI QABUL QILISH
# VA PREVIEW
# =========================================================

@dp.message(
    AdForm.selling_comment,
    F.text
)
async def receive_selling_comment(
    message: Message,
    state: FSMContext
):

    if message.text == "Bekor qilish":

        await state.clear()

        await message.answer(
            "🏠 <b>Asosiy menyuga qaytdingiz.</b>\n\n"
            "Kerakli bo‘limni tanlang 👇",
            reply_markup=main_menu()
        )

        return

    comment = message.text.strip()

    data = await state.get_data()

    account_photo = data.get(
        "account_photo"
    )

    google_gamecenter = data.get(
        "google_gamecenter"
    )

    exchange = data.get(
        "exchange"
    )

    selling_type = data.get(
        "selling_type"
    )

    price = data.get(
        "price"
    )

    # =====================================================
    # USERNAME
    # =====================================================

    username = message.from_user.username

    user_id = message.from_user.id

    if username:

        contact_text = f"@{username}"

        contact_link = (
            f"https://t.me/{username}"
        )

    else:

        contact_text = "Profilga o'tish"

        contact_link = (
            f"tg://user?id={user_id}"
        )

    # =====================================================
    # STATUS
    # =====================================================

    if selling_type == "faqat_obmen":

        status_text = (
            "#SOTILMAYDI "
            "#FAQAT_OBMEN"
        )

    else:

        status_text = "#SOTILADI"

    # =====================================================
    # GOOGLE / GAME CENTER
    # =====================================================

    if google_gamecenter == "✅":

        google_text = "Ulangan"

    else:

        google_text = "Ulanmagan"

    # =====================================================
    # OBMEN
    # =====================================================

    if exchange == "✅":

        exchange_text = "Bor"

    else:

        exchange_text = "Yo‘q"

    # =====================================================
    # AKKAUNT NARXI
    # =====================================================

    if selling_type == "faqat_obmen":

        price_text = "OBMEN UCHUN"

    else:

        price_text = (
            f"{price} so'm"
            if price
            else "Ko‘rsatilmagan"
        )

    # =====================================================
    # XIZMAT NARXI
    # =====================================================

    service_price = get_service_price(
        selling_type,
        price
    )

    service_price_text = (
        f"{service_price:,}"
        .replace(",", " ")
        + " so'm"
    )

    # =====================================================
    # PREVIEW
    # =====================================================

    preview_text = (
        f"<b>{status_text}</b>\n\n"

        f"💵 <b>Narx:</b> "
        f"<code>{price_text}</code>\n"

        f"🔄 <b>Obmen:</b> "
        f"{exchange_text}\n"

        f"⚠️ <b>Google &amp; Game Center:</b> "
        f"{google_text}\n"

        f"📱 <b>Murojaat:</b> "
        f"<a href=\"{contact_link}\">"
        f"{contact_text}"
        f"</a>\n\n"

        f"📝 <b>Qo‘shilgan ma'lumot:</b>\n"
        f"<blockquote>{comment}</blockquote>\n\n"

        f"🟢 <b>OLDI SOTDI GARANT ADMINLAR</b>\n"
        f"<blockquote>"
        f"@khasanow17"
        f"</blockquote>\n\n"

        f"🔻 <b>E'LON BERISH UCHUN BOTIMIZ</b>\n"
        f"<blockquote>"
        f"@EFShopUzBot"
        f"</blockquote>"
    )

    # =====================================================
    # PREVIEWNI YUBORISH
    # =====================================================

    if account_photo:

        await message.answer_photo(
            photo=account_photo,
            caption=preview_text,
            reply_markup=ReplyKeyboardRemove()
        )

    else:

        await message.answer(
            preview_text,
            reply_markup=ReplyKeyboardRemove()
        )

    # =====================================================
    # TO'LOV TUGMALARI
    # =====================================================

    payment_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="💳 Karta raqamiga to‘lov"
                )
            ],
            [
                KeyboardButton(
                    text="✅ To‘lov qildim"
                )
            ],
            [
                KeyboardButton(
                    text="🚫 Bekor qilish"
                )
            ]
        ],
        resize_keyboard=True
    )

    # =====================================================
    # TO'LOVGA TAYYOR XABAR
    # =====================================================

    payment_text = (
        "📢 <b>E'lon yuborishga tayyor!</b>\n\n"

        f"<blockquote>"
        f"📲 <b>Kanalimiz:</b> "
        f"@EFShop_UZ\n\n"

        f"💰 <b>Xizmat narxi:</b> "
        f"{service_price_text}\n\n"

        f"⏳ <b>5 daqiqa ichida to‘lov qiling.</b>\n\n"

        f"To‘lov qabul qilinishi bilan "
        f"e’lon kanalga avtomatik joylanadi.\n\n"

        f"(Avto-joylanmasa, vaqt tugagach "
        f"chekni yuborishingiz mumkin.)"
        f"</blockquote>"
    )

    await message.answer(
        payment_text,
        reply_markup=payment_keyboard
    )

    # =====================================================
    # MA'LUMOTLARNI SAQLASH
    # =====================================================

    await state.update_data(
        comment=comment,
        contact_username=contact_text,
        contact_link=contact_link,
        service_price=service_price,
        preview_text=preview_text
    )

    await state.set_state(
        AdForm.payment_waiting
    )
# =========================================================
# KARTA RAQAMIGA TO'LOV
# =========================================================

@dp.message(
    AdForm.payment_waiting,
    F.text == "💳 Karta raqamiga to‘lov"
)
async def card_payment(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    service_price = data.get(
        "service_price",
        5000
    )

    service_price_text = (
        f"{service_price:,}"
        .replace(",", " ")
        + " so'm"
    )

    payment_info = (
        "💳 <b>TO‘LOV UCHUN KARTA</b>\n\n"

        f"💳 <b>Karta raqami:</b>\n"
        f"<code>{CARD_NUMBER}</code>\n\n"

        f"👤 <b>Karta egasi:</b>\n"
        f"<code>{CARD_OWNER}</code>\n\n"

        f"💰 <b>To‘lov:</b> "
        f"<code>{service_price_text}</code>\n\n"

        "⚠️ <b>To‘lovni amalga oshirgach:</b>\n"
        "«✅ To‘lov qildim» tugmasini bosing."
    )

    payment_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="💳 Karta raqamiga to‘lov"
                )
            ],
            [
                KeyboardButton(
                    text="✅ To‘lov qildim"
                )
            ],
            [
                KeyboardButton(
                    text="🚫 Bekor qilish"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        payment_info,
        reply_markup=payment_keyboard
    )


# =========================================================
# TO'LOV QILDIM
# =========================================================

@dp.message(
    AdForm.payment_waiting,
    F.text == "✅ To‘lov qildim"
)
async def payment_done(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    # -----------------------------------------------------
    # E'LON MA'LUMOTLARINI SAQLAYMIZ
    # -----------------------------------------------------

    pending_ads[message.from_user.id] = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "account_photo": data.get("account_photo"),
        "google_gamecenter": data.get(
            "google_gamecenter"
        ),
        "exchange": data.get("exchange"),
        "selling_type": data.get(
            "selling_type"
        ),
        "price": data.get("price"),
        "comment": data.get("comment"),
        "contact_username": data.get(
            "contact_username"
        ),
        "contact_link": data.get(
            "contact_link"
        ),
        "service_price": data.get(
            "service_price"
        ),
        "preview_text": data.get(
            "preview_text"
        ),
    }

    # -----------------------------------------------------
    # ADMIN TASDIQLASH TUGMALARI
    # -----------------------------------------------------

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=(
                        f"approve_ad:"
                        f"{message.from_user.id}"
                    )
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=(
                        f"reject_ad:"
                        f"{message.from_user.id}"
                    )
                )
            ]
        ]
    )

    # -----------------------------------------------------
    # MIJOZ USERI
    # -----------------------------------------------------

    username = message.from_user.username

    if username:

        admin_user = f"@{username}"

    else:

        admin_user = "Username mavjud emas"

    # -----------------------------------------------------
    # XIZMAT NARXI
    # -----------------------------------------------------

    service_price = data.get(
        "service_price",
        5000
    )

    service_price_text = (
        f"{service_price:,}"
        .replace(",", " ")
        + " so'm"
    )

    # -----------------------------------------------------
    # ADMIN UCHUN XABAR
    # -----------------------------------------------------

    admin_text = (
        "💰 <b>YANGI TO‘LOV TASDIG‘I</b>\n\n"

        f"👤 <b>Mijoz:</b> "
        f"<a href=\"{data.get('contact_link')}\">"
        f"{admin_user}"
        f"</a>\n"

        f"💵 <b>Xizmat narxi:</b> "
        f"<code>{service_price_text}</code>\n\n"

        "📋 <b>E'lonni tekshiring.</b>\n"
        "To‘lovni tasdiqlasangiz, "
        "e'lon kanalga avtomatik joylanadi."
    )

    # -----------------------------------------------------
    # ADMIN GA RASM + XABAR
    # -----------------------------------------------------

    if data.get("account_photo"):

        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=data["account_photo"],
            caption=admin_text,
            reply_markup=admin_keyboard
        )

    else:

        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=admin_keyboard
        )

    # -----------------------------------------------------
    # MIJOZGA XABAR
    # -----------------------------------------------------

    await state.set_state(
        AdForm.payment_submitted
    )

    await message.answer(
        "⏳ <b>To‘lovingiz admin tasdig‘iga "
        "yuborildi.</b>\n\n"

        "🛡 Admin to‘lovni tasdiqlaganidan so‘ng "
        "e’loningiz avtomatik ravishda "
        "<b>@EFShop_UZ</b> kanaliga joylanadi.",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# ADMIN — E'LONNI TASDIQLASH
# =========================================================

@dp.callback_query(
    F.data.startswith("approve_ad:")
)
async def approve_ad(
    callback: CallbackQuery
):

    # -----------------------------------------------------
    # FAQAT ADMIN
    # -----------------------------------------------------

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "❌ Sizda ruxsat yo‘q!",
            show_alert=True
        )

        return

    # -----------------------------------------------------
    # USER ID
    # -----------------------------------------------------

    user_id = int(
        callback.data.split(":")[1]
    )

    # -----------------------------------------------------
    # E'LONNI OLAMIZ
    # -----------------------------------------------------

    ad = pending_ads.get(user_id)

    if not ad:

        await callback.answer(
            "⚠️ Bu e'lon topilmadi yoki "
            "allaqachon ko‘rib chiqilgan.",
            show_alert=True
        )

        return

    # -----------------------------------------------------
    # KANALGA JOYLASH
    # -----------------------------------------------------

    try:

        if ad.get("account_photo"):

            await bot.send_photo(
                chat_id=CHANNEL_USERNAME,
                photo=ad["account_photo"],
                caption=ad["preview_text"]
            )

        else:

            await bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=ad["preview_text"]
            )

    except Exception as error:

        await callback.answer(
            "❌ Kanalga joylashda xatolik!",
            show_alert=True
        )

        print(
            f"Kanalga yuborishda xatolik: {error}"
        )

        return

    # -----------------------------------------------------
    # PENDINGDAN O'CHIRAMIZ
    # -----------------------------------------------------

    pending_ads.pop(
        user_id,
        None
    )

    # -----------------------------------------------------
    # MIJOZGA XABAR
    # -----------------------------------------------------

    try:

        await bot.send_message(
            chat_id=user_id,
            text=(
                "✅ <b>E'loningiz tasdiqlandi!</b>\n\n"
                "📢 E'loningiz "
                "<b>@EFShop_UZ</b> kanaliga "
                "avtomatik joylandi."
            )
        )

    except Exception as error:

        print(
            f"Mijozga xabar yuborishda xatolik: "
            f"{error}"
        )

    # -----------------------------------------------------
    # ADMIN TUGMALARINI OLIB TASHLASH
    # -----------------------------------------------------

    try:

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

    except Exception:
        pass

    await callback.answer(
        "✅ E'lon kanalga joylandi!"
    )


# =========================================================
# ADMIN — E'LONNI RAD ETISH
# =========================================================

@dp.callback_query(
    F.data.startswith("reject_ad:")
)
async def reject_ad(
    callback: CallbackQuery
):

    # -----------------------------------------------------
    # FAQAT ADMIN
    # -----------------------------------------------------

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "❌ Sizda ruxsat yo‘q!",
            show_alert=True
        )

        return

    # -----------------------------------------------------
    # USER ID
    # -----------------------------------------------------

    user_id = int(
        callback.data.split(":")[1]
    )

    # -----------------------------------------------------
    # E'LONNI OLAMIZ
    # -----------------------------------------------------

    ad = pending_ads.get(user_id)

    if not ad:

        await callback.answer(
            "⚠️ Bu e'lon topilmadi yoki "
            "allaqachon ko‘rib chiqilgan.",
            show_alert=True
        )

        return

    # -----------------------------------------------------
    # PENDINGDAN O'CHIRAMIZ
    # -----------------------------------------------------

    pending_ads.pop(
        user_id,
        None
    )

    # -----------------------------------------------------
    # MIJOZGA XABAR
    # -----------------------------------------------------

    try:

        await bot.send_message(
            chat_id=user_id,
            text=(
                "❌ <b>To‘lov tasdiqlanmadi.</b>\n\n"
                "Iltimos, admin bilan bog‘laning:\n"
                "🛡 @khasanow17"
            )
        )

    except Exception as error:

        print(
            f"Mijozga rad javobi yuborishda "
            f"xatolik: {error}"
        )

    # -----------------------------------------------------
    # ADMIN TUGMALARINI OLIB TASHLASH
    # -----------------------------------------------------

    try:

        await callback.message.edit_reply_markup(
            reply_markup=None
        )

    except Exception:
        pass

    await callback.answer(
        "❌ E'lon rad etildi."
    )


# =========================================================
# OLISH E'LONI
# =========================================================

@dp.message(
    F.text == "🔻 Olish e'loni"
)
async def buy_ad(
    message: Message,
    state: FSMContext
):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Botdan foydalanish uchun "
            "kanalimizga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    await state.clear()

    await state.set_state(
        AdForm.buying
    )

    cancel_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Bekor qilish"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "🔻 <b>Olish e'loni</b>\n\n"
        "🔎 <b>Qanday akkaunt "
        "qidirayotganingizni yozing:</b>",
        reply_markup=cancel_keyboard
    )


# =========================================================
# OLISH E'LONI MATNI
# =========================================================

@dp.message(
    AdForm.buying,
    F.text
)
async def receive_buying(
    message: Message,
    state: FSMContext
):

    if message.text == "Bekor qilish":

        await state.clear()

        await message.answer(
            "🏠 <b>Asosiy menyuga qaytdingiz.</b>\n\n"
            "Kerakli bo‘limni tanlang 👇",
            reply_markup=main_menu()
        )

        return

    await state.update_data(
        buying_text=message.text
    )


# =========================================================
# BEKOR QILISH
# =========================================================

@dp.message(
    F.text == "Bekor qilish"
)
async def cancel_ad(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "🏠 <b>Asosiy menyuga qaytdingiz.</b>\n\n"
        "Kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu()
    )


# =========================================================
# 🚫 BEKOR QILISH
# =========================================================

@dp.message(
    F.text == "🚫 Bekor qilish"
)
async def cancel_payment(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "🏠 <b>Asosiy menyuga qaytdingiz.</b>\n\n"
        "Kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu()
    )


# =========================================================
# ORQAGA
# =========================================================

@dp.message(
    F.text == "🔙 Orqaga"
)
async def back_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Kerakli bo‘limni tanlang 👇",
        reply_markup=main_menu()
    )


# =========================================================
# AKKAUNT QIDIRISH
# =========================================================

@dp.message(
    F.text == "🔎 Akkaunt qidirish"
)
async def search_account(
    message: Message,
    state: FSMContext
):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Botdan foydalanish uchun "
            "kanalimizga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    await state.clear()

    await message.answer(
        "🔎 <b>Akkaunt qidirish</b>\n\n"
        "Hozircha bu bo‘lim tayyorlanmoqda.",
        reply_markup=back_menu()
    )


# =========================================================
# E'LONLARIM
# =========================================================

@dp.message(
    F.text == "📂 E'lonlarim"
)
async def my_ads(
    message: Message,
    state: FSMContext
):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Botdan foydalanish uchun "
            "kanalimizga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    await state.clear()

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="➕ E'lon berish"
                )
            ],
            [
                KeyboardButton(
                    text="🔙 Orqaga"
                )
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "📂 <b>E'lonlarim</b>\n\n"
        "Sizda hozircha e'lonlar mavjud emas.",
        reply_markup=keyboard
    )


# =========================================================
# ADMINLAR
# =========================================================

@dp.message(
    F.text == "🛡 Adminlar"
)
async def admins(
    message: Message,
    state: FSMContext
):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Botdan foydalanish uchun "
            "kanalimizga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    await state.clear()

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 GARANT | ADMIN",
                    url="https://t.me/khasanow17"
                )
            ]
        ]
    )

    await message.answer(
        "🛡 <b>Adminlar</b>\n\n"
        "📱 @khasanow17",
        reply_markup=admin_keyboard
    )

    await message.answer(
        "Kerakli bo‘limga qaytish uchun:",
        reply_markup=back_menu()
    )


# =========================================================
# QOIDALAR
# =========================================================

@dp.message(
    F.text == "📚 Qoidalar"
)
async def rules(
    message: Message,
    state: FSMContext
):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Botdan foydalanish uchun "
            "kanalimizga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    await state.clear()

    rules_text = (
        "📚 <b>EF SHOP UZ — QOIDALAR</b>\n\n"

        "1️⃣ E'lon berishda akkaunt haqida aniq "
        "va to‘liq ma'lumot berish kerak.\n\n"

        "2️⃣ Aldov, firibgarlik yoki yolg‘on "
        "ma'lumot berish qat'iyan taqiqlanadi.\n\n"

        "3️⃣ Akkaunt rasmini namunadagidek "
        "sifatli yuboring.\n\n"

        "4️⃣ Narxni aniq ko‘rsating.\n\n"

        "5️⃣ Obmen bo‘lsa, bu haqda e'londa "
        "aniq ko‘rsatiladi.\n\n"

        "6️⃣ Boshqa foydalanuvchilarni aldash "
        "yoki chalg‘itish uchun e'lonlardan "
        "foydalanish taqiqlanadi.\n\n"

        "7️⃣ Adminlar qoidabuzarlik aniqlangan "
        "e'lonni o‘chirish huquqiga ega.\n\n"

        "8️⃣ Shubhali holatlarda admin bilan "
        "bog‘laning.\n\n"

        "🛡 <b>EF SHOP UZ</b>"
    )

    await message.answer(
        rules_text,
        reply_markup=back_menu()
    )


# =========================================================
# E'LON NARXLARI
# =========================================================

@dp.message(
    F.text == "💰 E'lon narxlari"
)
async def ad_prices(
    message: Message,
    state: FSMContext
):

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Botdan foydalanish uchun "
            "kanalimizga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    await state.clear()

    prices_text = (
        "💰 <b>E'lon berish narxlari</b>\n\n"

        "💵 <b>0 — 500 000 so‘m</b>\n"
        "➡️ E'lon narxi: <b>5 000 so‘m</b>\n\n"

        "💵 <b>500 001 — 1 500 000 so‘m</b>\n"
        "➡️ E'lon narxi: <b>7 000 so‘m</b>\n\n"

        "💵 <b>1 500 001 so‘mdan yuqori</b>\n"
        "➡️ E'lon narxi: <b>10 000 so‘m</b>"
    )

    await message.answer(
        prices_text,
        reply_markup=back_menu()
    )


# =========================================================
# NOMA'LUM XABARLAR
# =========================================================

@dp.message()
async def unknown_message(
    message: Message,
    state: FSMContext
):

    current_state = await state.get_state()

    if current_state:
        return

    subscribed = await check_subscription(
        message.from_user.id
    )

    if not subscribed:

        await message.answer(
            "❌ Avval kanalimizga obuna bo‘ling.",
            reply_markup=subscription_keyboard()
        )

        return

    await message.answer(
        "👇 <b>Kerakli bo‘limni tanlang:</b>",
        reply_markup=main_menu()
    )


# =========================================================
# BOTNI ISHGA TUSHIRISH
# =========================================================

async def main():

    print(
        "EFShopUzBot ishga tushdi..."
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())