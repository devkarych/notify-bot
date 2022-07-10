from sqlalchemy import delete, select, func
from sqlalchemy.orm import sessionmaker

from app.models import dto, database
from app.models.database import Reminder
from app.services.database.dao.base import BaseDAO


class ReminderDAO(BaseDAO[Reminder]):
    """ORM queries for reminders table"""

    def __init__(self, session: sessionmaker):
        super().__init__(Reminder, session)

    async def add_reminder(self, reminder: dto.Reminder) -> dto.Reminder:
        """
        Add reminder to database if not added yet.
        :param reminder:
        """

        async with self._session() as session:
            await session.merge(_map_to_db_reminder(reminder))
            await session.commit()
            return reminder

    async def remove_reminder(self, reminder_id: int) -> None:
        """
        Removes reminder from database.
        :param reminder_id:
        """

        async with self._session() as session:
            await session.execute(
                delete(database.Reminder).where(database.Reminder.id == reminder_id)
            )
            await session.commit()

    async def get_reminders_count_by_user_id(self, user_id: int) -> int:
        """Returns active reminders count by user id"""

        async with self._session() as session:
            executed = await session.execute(select(func.count()).
                                             select_from(select(Reminder).
                                                         where(Reminder.user_id == user_id).
                                                         subquery()))
            count = executed.scalar_one()
            return count


def _map_to_db_reminder(reminder: dto.Reminder) -> database.Reminder:
    """
    Maps DTO -> database reminder
    :param reminder:
    :return: database reminder
    """

    return database.Reminder(
        user_id=reminder.owner_id,
        text=reminder.text,
        notify_time=reminder.notify_time
    )
