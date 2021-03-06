import datetime

from aiogram.utils.markdown import hcode as mono

from app.models import dto

enter_reminder_text = "✍ <i>Введи <b>текст напоминалки</b> одним сообщением:</i>"
set_time_on_calendar = "<i>Отлично! Теперь выбери <b>дату</b> отправки напоминалки:</i>"


def set_hours(submitted_date: datetime.datetime) -> str:
    """Message to submit hours"""
    return f"<i>Дата отправки: {submitted_date.strftime('%d/%m/%Y')}\n\n" \
           f"⏰ <b>Выбери час отправки:</b></i>"


def set_minutes(submitted_date: datetime.datetime) -> str:
    """Message to submit minutes"""
    return f"<i>Дата отправки: {submitted_date.strftime('%d/%m/%Y')}.\n" \
           f"Время отправки: {submitted_date.hour}:X.\n\n" \
           f"⏰ <b>Выбери минуту отправки:</b></i>"


def reminder_created(submitted_date: datetime.datetime) -> str:
    """Reminder created correctly"""
    return f"<i>Дата отправки: {submitted_date.strftime('%d/%m/%Y')}.\n" \
           f"Время отправки: {submitted_date.strftime('%H:%M')}.\n\n" \
           f"👍 <b>Молодец, все данные заполнены, так держать!</b></i>"


def date_missed(submitted_date: datetime.datetime) -> str:
    """Submitted date already been in the past"""
    return f"<i> ❌ <b>Напоминалка не создана</b>\n\nИзвиняй. Дата и время: " \
           f"<b>{submitted_date.strftime('%d/%m/%Y')}; {submitted_date.strftime('%H:%M')}</b> " \
           f"некорректны, так как нельзя создать напоминалку в прошлом...</i>"


reminder_limit_exceeded = "<i> ❌ <b>Напоминалка не создана</b>\n\nИзвиняй. " \
                          "Нельзя создать больше 10 напоминалок. Либо удаляй лишние, " \
                          "либо подожди</i>"

return_to_default_menu = "🔙  <i>Возвращаемся в главное меню!</i>"


def reminder_about(reminder: dto.Reminder) -> str:
    """Returns reminder about message"""
    utc_3_hour = (reminder.notify_time.hour + 3) % 24
    reminder.notify_time = reminder.notify_time.replace(hour=utc_3_hour)
    return f"<i>{mono(reminder.text)}\n\nВремя отправки: " \
           f"{reminder.notify_time.strftime('%d/%m/%Y')}; " \
           f"{reminder.notify_time.strftime('%H:%M')}</i>"


no_added_reminders = "<i>У тебя пока нет добавленных напоминалок</i>"
