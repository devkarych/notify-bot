import asyncio
import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import CallbackQuery, ChatActions

from app.core.keyboards import reply, inline
from app.core.keyboards.calendar import Calendar, calendar_callback
from app.core.messages.private_chat import reminder as msgs
from app.core.middlewares.throttling import throttle
from app.core.navigations import reply as reply_nav, inline as inline_nav
from app.core.navigations.reply import cancel
from app.core.states.reminder import ReminderAddition
from app.models.dto import Reminder, get_user_from_message
from app.services.database.dao.reminder import ReminderDAO


async def btn_cancel(m: types.Message, state: FSMContext):
    """Universal canceller from any state"""

    await m.reply("<b>Отмена!</b>", reply_markup=reply.default)
    await state.finish()


@throttle(limit=2)
async def btn_add_reminder(m: types.Message):
    """Add reminder command handling"""

    await m.answer(msgs.enter_reminder_text, reply_markup=reply.cancel)
    await ReminderAddition.text.set()


@throttle(limit=2)
async def state_submit_reminder(m: types.Message, state: FSMContext):
    """Adds reminder text to memory storage"""

    async with state.proxy() as data:
        data['reminder'] = m.parse_entities()

    await m.reply(msgs.set_time_on_calendar, reply_markup=await Calendar().start_calendar())
    await ReminderAddition.date.set()


async def calendar_process(call: CallbackQuery, state: FSMContext, callback_data: dict):
    """Calendar date choosing process"""

    selected, date = await Calendar().process_selection(call, callback_data)
    if selected:
        async with state.proxy() as data:
            data['date']: datetime.datetime = date
            await call.message.edit_text(msgs.set_hours(submitted_date=date))
            await call.message.edit_reply_markup(inline.hours())

        await ReminderAddition.hours.set()


async def submit_hours(call: CallbackQuery, state: FSMContext):
    """User submitted the hour by inl button click"""

    async with state.proxy() as data:
        submitted_hour = int(call.data.replace("hour_", ""))
        data['date'] = data['date'].replace(hour=submitted_hour)

        await call.message.edit_text(msgs.set_minutes(data['date']))
        await call.message.edit_reply_markup(inline.minutes())

    await ReminderAddition.minutes.set()


async def submit_minutes(call: CallbackQuery, state: FSMContext):
    """User submitted the minute by inl button click. Last part of reminder creation"""

    await call.message.edit_reply_markup(None)
    reminders_count_limit = 10

    async with state.proxy() as data:
        submitted_minute = int(call.data.replace("minute_", ""))
        # Now, date is ready
        data['date'] = data['date'].replace(minute=submitted_minute)

        # Check if date is in the future
        if datetime.datetime.now() < data['date']:
            dao = ReminderDAO(session=call.bot.get("db"))
            # Check if reminders limit does not exceeded
            if await dao.get_reminders_count_by_user_id(user_id=call.from_user.id) < \
                    reminders_count_limit:
                await call.message.edit_text(msgs.reminder_created(data['date']))

                # Adding reminder to database
                await dao.add_reminder(
                    reminder=Reminder(
                        owner_id=call.from_user.id,
                        notify_time=data['date'],
                        text=data['reminder']
                    ))
            # Reminders limit exceeded
            else:
                await call.message.edit_text(msgs.reminder_limit_exceeded)
        # Date is missed
        else:
            await call.message.edit_text(msgs.date_missed(submitted_date=data['date']))

    await call.message.answer_chat_action(ChatActions.TYPING)
    await asyncio.sleep(1)
    await call.message.answer(msgs.return_to_default_menu, reply_markup=reply.default)
    await state.finish()


async def btn_get_reminders_list(m: types.Message):
    """Displays list of current """
    user = get_user_from_message(message=m)
    rem_dao = ReminderDAO(session=m.bot.get("db"))
    reminders = await rem_dao.get_user_reminders(user_id=user.id)

    if reminders:
        for reminder in reminders:
            await m.answer_chat_action(ChatActions.TYPING)
            await asyncio.sleep(0.3)
            await m.answer(msgs.reminder_about(reminder),
                           reply_markup=inline.reminder_params(reminder_id=reminder.id))

    # No added reminders. `reminders` is empty
    else:
        await m.answer(msgs.no_added_reminders)


async def btn_delete_reminder(call: CallbackQuery):
    """Removing reminder by button click"""

    # Some magic parsing =)
    reminder_id = int(call.data.replace(inline_nav.delete_reminder.callback + "_", ""))

    rem_dao = ReminderDAO(session=call.bot.get("db"))
    await rem_dao.remove_reminder(reminder_id=reminder_id)

    await call.message.edit_reply_markup(None)
    await call.message.delete()


def register_handlers(dp: Dispatcher) -> None:
    """Register handlers for reminders interaction (addition, deletion, list-printing etc.)"""

    dp.register_message_handler(btn_add_reminder, Text(equals=[reply_nav.add_reminder]))
    dp.register_message_handler(btn_cancel, Text(equals=[cancel]), state="*")
    dp.register_message_handler(state_submit_reminder, state=ReminderAddition.text)
    dp.register_message_handler(btn_get_reminders_list, Text(equals=[reply_nav.reminder_list]))

    dp.register_callback_query_handler(btn_delete_reminder,
                                       Text(contains=[inline_nav.delete_reminder.callback]))
    dp.register_callback_query_handler(submit_hours, state=ReminderAddition.hours)
    dp.register_callback_query_handler(submit_minutes, state=ReminderAddition.minutes)
    dp.register_callback_query_handler(calendar_process,
                                       calendar_callback.filter(),
                                       state=ReminderAddition.date)
