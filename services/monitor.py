import asyncio
from aiogram import Bot

from api.freelancehunt import FreelancehuntAPI
from database.storage import is_project_sent, save_sent_project
from bot.layouts import format_project_notification
from bot.keyboards import project_keyboard
from config import settings
from utils.logger import logger

fh_api = FreelancehuntAPI()


def _project_skill_ids(project: dict) -> set:
    skills = project.get("attributes", {}).get("skills", []) or []
    out = set()
    for s in skills:
        sid = s.get("id")
        if isinstance(sid, int):
            out.add(sid)
    return out


def _passes_skill_filter(project: dict) -> bool:
    """If FILTER_SKILL_IDS is empty — accept everything. Otherwise project
    must have at least one skill from the configured set."""
    target = settings.filter_skill_ids_set
    if not target:
        return True
    return bool(_project_skill_ids(project) & target)


async def start_monitoring(bot: Bot):
    logger.info("Monitoring service started")
    chat_ids = settings.chat_ids_list
    if not chat_ids:
        logger.error("CHAT_ID is empty — nothing to send. Aborting monitor loop.")
        return
    skill_filter = settings.filter_skill_ids_set
    if skill_filter:
        logger.info(f"Skill filter active: only projects with any of {sorted(skill_filter)}")
    logger.info(f"Will broadcast to {len(chat_ids)} chat(s): {chat_ids}")

    while True:
        try:
            projects = fh_api.get_new_projects()
            for project in projects:
                p_id = int(project["id"])

                if not _passes_skill_filter(project):
                    # Mark as "seen" так само як надіслане — щоб на наступних
                    # ітераціях не перепарсити одне й те саме сотні разів.
                    if not await is_project_sent(p_id):
                        await save_sent_project(p_id)
                    continue

                if await is_project_sent(p_id):
                    continue

                attrs = project["attributes"]
                employer_id = attrs.get("employer", {}).get("id")
                stats = ""
                if employer_id:
                    emp_info = fh_api.get_employer_info(employer_id)
                    rating = emp_info.get("rating", 0)
                    pos = emp_info.get("positive_reviews", 0)
                    neg = emp_info.get("negative_reviews", 0)
                    stats = f"(⭐ {rating} | 👍{pos} 👎{neg})"

                text = format_project_notification(project, stats)
                url = fh_api.get_project_link(p_id, attrs.get("name", ""))
                kb = project_keyboard(url)

                # Broadcast to ALL configured chats. Якщо хоча б один send
                # пройшов — вважаємо проєкт обробленим (інакше будемо
                # ретраїти весь broadcast при кожній ітерації).
                any_sent = False
                for chat_id in chat_ids:
                    try:
                        await bot.send_message(chat_id=chat_id, text=text, reply_markup=kb)
                        any_sent = True
                        await asyncio.sleep(0.3)  # rate-limit per chat
                    except Exception as e:
                        logger.error(f"Send to {chat_id} failed for project {p_id}: {e}")

                if any_sent:
                    await save_sent_project(p_id)
                    logger.info(f"New project sent: {attrs.get('name')}")
                else:
                    logger.warning(f"Project {p_id} not marked sent — all chats failed")

                await asyncio.sleep(1)  # пауза між проєктами

        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")

        await asyncio.sleep(30)  # пауза між API-poll'ами
