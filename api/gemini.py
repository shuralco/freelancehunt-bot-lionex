import json
import logging
import aiohttp
import html
from config import settings
from bio import BIO
from utils.logger import logger

class GeminiService:
    def __init__(self):
        self.keys = settings.gemini_keys_list
        self.url_template = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={}"

    def _prepare_prompt(self, project_text: str) -> str:
        skills_str = "\n- ".join(BIO["main_skills"])
        portfolio_str = "\n".join([f"- {p['title']}: {p['url']}" for p in BIO["portfolio"]])
        
        prompt = f"""Ты — интеллектуальный ассистент фрилансера по имени {BIO['name']}. 
Твоя задача: проанализировать проект и составить идеальный отклик + инструкцию.

ДАННЫЕ ФРИЛАНСЕРА:
Имя: {BIO['name']}
Специализация: {BIO['specialization']}
Навыки:
- {skills_str}

Портфолио (используй ссылки, только если они подходят по теме):
{portfolio_str}

ПРАВИЛА ОТВЕТА (СТРОГО):
1. ЯЗЫК ОТВЕТА: ВСЕГДА украинский, независимо от языка проекта. Если описание на русском, английском или другом — переводи и отвечай украинским. Никогда не используй русский язык в ответе.
2. ОТКЛИК:
    - Природний живий тон, без штампів типу «Доброго дня! Ваш проект цікавий».
    - 2-3 короткі речення.
    - Якщо задача підходить під портфоліо — згадай це й встав ОДНЕ найрелевантніше посилання зі списку.
    - Якщо проєкт поза твоєю компетенцією — пиши «Маю досвід у схожих задачах, готовий обговорити деталі».
    - Формат: «Вітаю, [імя замовника якщо є]! ... готовий допомогти ... [кейс із портфоліо] ... Буду радий обговорити!»
3. ІНСТРУКЦІЯ ПО ВИКОНАННЮ:
    - Конкретний покроковий алгоритм (1, 2, 3) — як Владислав/команда Lionex може виконати цю задачу: технології, етапи, ключові інтеграції.
4. ОЦІНКА (СКОРИНГ):
    - На початку інструкції постав оцінку складності від 1 до 5 і релевантність зірочками (⭐⭐⭐⭐⭐).

СТРУКТУРА ОТВЕТА:
[ОТКЛИК]
(текст отклика)

[ИНСТРУКЦИЯ]
(оценка и пошаговый план)

ТЕКСТ ПРОЕКТА:
{project_text}"""
        return prompt

    async def generate_response(self, project_text: str) -> str:
        prompt = self._prepare_prompt(project_text)
        
        for key in self.keys:
            url = self.url_template.format(key)
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7}
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=20) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data['candidates'][0]['content']['parts'][0]['text'].strip()
                        else:
                            logger.warning(f"Gemini key failed (status {resp.status})")
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                
        return "❌ Не удалось сгенерировать отклик. Все лимиты исчерпаны."

gemini_service = GeminiService()
