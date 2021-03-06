import asyncio
from contextlib import suppress
from datetime import datetime

import pytz
from aiogram import Bot
from aiogram.utils.exceptions import BotBlocked, InvalidUserId, UserDeactivated

from app.models import dto
from app.services.database.dao.reminder import ReminderDAO


async def setup_notificator(bot: Bot) -> None:
    """
    Get reminders from database. Manage tasks. Notify users.
    :param bot: Initialized bot instance for sending notifications.
    """

    rems_dao = ReminderDAO(session=bot.get("db"))

    reminders = await rems_dao.get_all()

    for _reminder in reminders:
        reminder = dto.Reminder.from_db(_reminder)

        if _is_date_came(
                current_datetime=datetime.now(tz=pytz.timezone("UTC")),
                reminder_datetime=reminder.notify_time
        ):
            with suppress(BotBlocked, InvalidUserId, UserDeactivated):
                await _send_notification(bot=bot, reminder=reminder)
            await rems_dao.remove_reminder(reminder_id=reminder.id)
            await asyncio.sleep(0.1)


def _is_date_came(current_datetime: datetime, reminder_datetime: datetime) -> bool:
    """
    Compares dates. Returns True if current datetime == reminder's notif datetime or
    reminder datetime is in the past.
    """

    return all((
        current_datetime.year == reminder_datetime.year,
        current_datetime.month == reminder_datetime.month,
        current_datetime.day == reminder_datetime.day,
        current_datetime.hour == reminder_datetime.hour,
        current_datetime.minute == reminder_datetime.minute
    )) or current_datetime > reminder_datetime


async def _send_notification(bot: Bot, reminder: dto.Reminder) -> None:
    """Notification message sending"""

    await bot.send_message(reminder.owner_id, f"🔔 <b>Напоминание:</b>\n\n{reminder.text}")
