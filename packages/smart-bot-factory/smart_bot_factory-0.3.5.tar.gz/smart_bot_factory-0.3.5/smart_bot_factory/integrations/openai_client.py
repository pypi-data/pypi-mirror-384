import logging
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Клиент для работы с OpenAI API"""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-4", 
        max_tokens: int = 1500,
        temperature: float = 0.7
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Настройки для повторных попыток
        self.max_retries = 3
        self.retry_delay = 1  # секунды
        
        # Определяем, является ли это GPT-5 моделью
        self.is_gpt5 = 'gpt-5' in model.lower()
        
        # Получаем лимиты для модели
        self.model_limits = self._get_model_limits()
        
        # 🆕 Для диагностики пустых ответов
        self.last_completion_tokens = 0
        
        logger.info(f"OpenAI клиент инициализирован с моделью {model} (GPT-5: {self.is_gpt5}, лимит: {self.model_limits['total_context']} токенов)")    
    
    def _get_model_limits(self) -> Dict[str, int]:
        """Возвращает лимиты для конкретной модели"""
        model_limits = {
            # GPT-3.5
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16385,
            
            # GPT-4
            'gpt-4': 8192,
            'gpt-4-32k': 32768,
            'gpt-4-turbo': 128000,
            'gpt-4-turbo-preview': 128000,
            'gpt-4o': 128000,
            'gpt-4o-mini': 128000,
            
            # GPT-5
            'gpt-5-mini': 128000,
            'gpt-5': 200000,
        }
        
        # Получаем лимит для текущей модели или используем консервативное значение
        total_limit = model_limits.get(self.model, 8192)
        
        # Резервируем место для ответа и буфера
        completion_reserve = min(self.max_tokens * 2, total_limit // 4)  # Резервируем место для ответа
        buffer_reserve = 500  # Буфер для безопасности
        
        return {
            'total_context': total_limit,
            'max_input_tokens': total_limit - completion_reserve - buffer_reserve,
            'completion_reserve': completion_reserve
        }
    
    def _get_completion_params(self, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Возвращает параметры для создания completion в зависимости от модели"""
        tokens = max_tokens or self.max_tokens
        temp = temperature or self.temperature
        
        params = {
            "model": self.model,
        }
        
        # 🆕 ИСПРАВЛЕННАЯ ЛОГИКА ДЛЯ GPT-5
        if self.is_gpt5:
            # 🔧 ИСПОЛЬЗУЕМ ТОКЕНЫ ИЗ КОНФИГА (как настроил пользователь)
            params["max_completion_tokens"] = tokens
            
            # 🔧 БЫСТРЫЕ ОТВЕТЫ с минимальным reasoning
            # Допустимые значения reasoning_effort:
            # "minimal" - самые быстрые ответы, минимальное reasoning
            # "low" - немного больше reasoning
            # "medium" - сбалансированное reasoning (медленнее)
            # "high" - максимальное reasoning (самые медленные, но качественные)
            params["reasoning_effort"] = "minimal"  # Быстрые ответы
            
            logger.debug(f"GPT-5 параметры: max_completion_tokens={tokens}, reasoning_effort=minimal")
        else:
            # Для остальных моделей стандартные параметры
            params["max_tokens"] = tokens
            params["temperature"] = temp
        
        return params

    async def get_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> str:
        """Получает ответ от OpenAI API с поддержкой GPT-5"""
        if not messages:
            raise ValueError("Список сообщений не может быть пустым")
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Отправка запроса к OpenAI (попытка {attempt + 1})")
                
                # Обрезаем сообщения если контекст слишком большой
                processed_messages = await self._prepare_messages(messages)
                
                # Получаем параметры в зависимости от модели
                params = self._get_completion_params(max_tokens, temperature)
                params["messages"] = processed_messages
                params["stream"] = stream
                
                logger.info(f"🚀 Отправляем запрос к {self.model}")
                logger.info(f"📝 Сообщений в контексте: {len(processed_messages)}")
                
                # Логируем параметры в зависимости от модели
                if self.is_gpt5:
                    max_tokens_param = params.get('max_completion_tokens')
                    reasoning_effort = params.get('reasoning_effort')
                    logger.info(f"⚙️ GPT-5 параметры: max_completion_tokens={max_tokens_param}, reasoning_effort={reasoning_effort}")
                else:
                    max_tokens_param = params.get('max_tokens')
                    temp_param = params.get('temperature')
                    logger.info(f"⚙️ Стандартные параметры: max_tokens={max_tokens_param}, temp={temp_param}")
                
                response: ChatCompletion = await self.client.chat.completions.create(**params)
                
                if stream:
                    return await self._handle_stream_response(response)
                else:
                    # 🔧 ПРАВИЛЬНЫЙ ПАРСИНГ ДЛЯ GPT-5 (может быть несколько choices)
                    if self.is_gpt5 and len(response.choices) > 1:
                        logger.info(f"📊 GPT-5 вернул {len(response.choices)} choices, ищем пользовательский контент")
                        
                        # Ищем choice с пользовательским контентом (не reasoning summary)
                        content = None
                        finish_reason = None
                        
                        for i, choice in enumerate(response.choices):
                            choice_content = choice.message.content
                            choice_finish = choice.finish_reason
                            
                            logger.info(f"   Choice {i}: content={len(choice_content) if choice_content else 0} chars, finish={choice_finish}")
                            
                            # Берем первый choice с реальным контентом
                            if choice_content and choice_content.strip():
                                content = choice_content
                                finish_reason = choice_finish
                                logger.info(f"   ✅ Используем choice {i} как пользовательский контент")
                                break
                        
                        # Если не нашли контент ни в одном choice
                        if not content:
                            logger.warning(f"   ❌ Не найден пользовательский контент ни в одном choice")
                            content = ""
                            finish_reason = response.choices[0].finish_reason
                    else:
                        # Стандартная обработка для не-GPT-5 или одного choice
                        finish_reason = response.choices[0].finish_reason
                        content = response.choices[0].message.content
                    
                    logger.info(f"📊 OpenAI ответ получен:")
                    logger.info(f"   🏁 Finish reason: {finish_reason}")
                    logger.info(f"   🔤 Тип content: {type(content)}")
                    logger.info(f"   📏 Длина: {len(content) if content else 0}")
                    
                    # Логируем использование токенов
                    if response.usage:
                        self.last_completion_tokens = response.usage.completion_tokens
                        
                        logger.info(f"💰 Использование токенов:")
                        logger.info(f"   📥 Prompt: {response.usage.prompt_tokens}")
                        logger.info(f"   📤 Completion: {response.usage.completion_tokens}")
                        logger.info(f"   🔢 Total: {response.usage.total_tokens}")
                        
                        # 🆕 ЛОГИРУЕМ REASONING TOKENS ДЛЯ GPT-5
                        if hasattr(response.usage, 'reasoning_tokens'):
                            reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
                            if reasoning_tokens > 0:
                                logger.info(f"   💭 Reasoning: {reasoning_tokens}")
                    
                    # 🔧 ИСПРАВЛЕННАЯ ОБРАБОТКА GPT-5
                    if self.is_gpt5:
                        # Проверяем, есть ли reasoning токены
                        reasoning_tokens = 0
                        if response.usage and hasattr(response.usage, 'reasoning_tokens'):
                            reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0)
                        
                        # Если есть reasoning но нет content, увеличиваем токены
                        if reasoning_tokens > 0 and (not content or not content.strip()):
                            logger.warning(f"🔧 GPT-5: reasoning_tokens={reasoning_tokens}, но content пустой")
                            
                            # Если это не последняя попытка, пробуем с большим количеством токенов
                            if attempt < self.max_retries - 1:
                                current_tokens = max_tokens or self.max_tokens
                                increased_tokens = min(current_tokens * 2, 8000)  # Удваиваем, максимум 8000
                                
                                logger.info(f"🔄 Пробуем с увеличенными токенами: {increased_tokens}")
                                return await self.get_completion(
                                    messages, 
                                    max_tokens=increased_tokens, 
                                    temperature=temperature, 
                                    stream=stream
                                )
                            else:
                                # Последняя попытка - возвращаем информативное сообщение
                                return "Извините, модель потратила время на анализ, но не смогла сформулировать ответ. Попробуйте переформулировать вопрос."
                    
                    # Обычная обработка finish_reason
                    if finish_reason == 'length':
                        logger.warning(f"⚠️ Модель достигла лимита токенов")
                        
                        if content and content.strip():
                            # Есть частичный контент - возвращаем его
                            return content
                        else:
                            # Нет контента - информируем пользователя
                            return "Ответ слишком длинный. Попробуйте задать более конкретный вопрос."
                    
                    elif finish_reason == 'stop':
                        logger.info(f"✅ Нормальное завершение")
                        
                    elif finish_reason == 'content_filter':
                        logger.warning(f"🚫 Ответ заблокирован фильтром контента")
                        return "Извините, не могу ответить на этот вопрос."
                    
                    # Детальное логирование содержимого
                    if content:
                        logger.info(f"   🔍 Начало (50 символов): '{content[:50]}'")
                        logger.info(f"   🔍 Конец (50 символов): '{content[-50:]}'")
                    else:
                        logger.warning(f"   ❌ content is None или пустой")
                    
                    return content or ""
                    
            except Exception as e:
                logger.warning(f"Ошибка при обращении к OpenAI (попытка {attempt + 1}): {e}")
                
                if attempt == self.max_retries - 1:
                    logger.error(f"Все попытки исчерпаны. Последняя ошибка: {e}")
                    raise
                
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        raise Exception("Не удалось получить ответ от OpenAI")
                    
    async def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Подготавливает сообщения для отправки в API
        Обрезает контекст если он слишком большой
        """
        # Более точная оценка токенов для русского текста
        def estimate_message_tokens(msg):
            content = msg.get('content', '')
            # Для русского текста: примерно 2.5-3 символа на токен
            return len(content) // 2.5
        
        total_estimated_tokens = sum(estimate_message_tokens(msg) for msg in messages)
        max_input_tokens = self.model_limits['max_input_tokens']
        
        if total_estimated_tokens <= max_input_tokens:
            return messages
        
        logger.info(f"Контекст слишком большой ({int(total_estimated_tokens)} токенов), обрезаем до {max_input_tokens}")
        
        # Сохраняем системные сообщения
        system_messages = [msg for msg in messages if msg.get('role') == 'system']
        other_messages = [msg for msg in messages if msg.get('role') != 'system']
        
        # Рассчитываем токены системных сообщений
        system_tokens = sum(estimate_message_tokens(msg) for msg in system_messages)
        available_tokens = max_input_tokens - system_tokens
        
        if available_tokens <= 0:
            logger.warning("Системные сообщения занимают весь доступный контекст")
            return system_messages
        
        # Берем последние сообщения, помещающиеся в доступные токены
        current_tokens = 0
        trimmed_messages = []
        
        for msg in reversed(other_messages):
            msg_tokens = estimate_message_tokens(msg)
            if current_tokens + msg_tokens > available_tokens:
                break
            trimmed_messages.insert(0, msg)
            current_tokens += msg_tokens
        
        result_messages = system_messages + trimmed_messages
        logger.info(f"Контекст обрезан до {len(result_messages)} сообщений (~{int(current_tokens + system_tokens)} токенов)")
        
        return result_messages
    
    async def _handle_stream_response(self, response) -> str:
        """Обрабатывает потоковый ответ"""
        full_content = ""
        
        async for chunk in response:
            if chunk.choices[0].delta.content is not None:
                full_content += chunk.choices[0].delta.content
        
        return full_content
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Анализирует настроение и намерения сообщения
        
        Args:
            text: Текст для анализа
        
        Returns:
            Словарь с результатами анализа
        """
        analysis_prompt = f"""
        Проанализируй следующее сообщение пользователя и определи:
        1. Настроение (позитивное/нейтральное/негативное)
        2. Уровень заинтересованности (1-10)
        3. Готовность к покупке (1-10)
        4. Основные возражения или вопросы
        5. Рекомендуемая стратегия ответа
        
        Сообщение: "{text}"
        
        Ответь в формате JSON:
        {{
            "sentiment": "positive/neutral/negative",
            "interest_level": 1-10,
            "purchase_readiness": 1-10,
            "objections": ["список возражений"],
            "key_questions": ["ключевые вопросы"],
            "response_strategy": "рекомендуемая стратегия"
        }}
        """
        
        try:
            # Для анализа настроения используем более низкую температуру если поддерживается
            temp = 0.3 if not self.is_gpt5 else None
            
            response = await self.get_completion([
                {"role": "system", "content": "Ты эксперт по анализу намерений клиентов в продажах."},
                {"role": "user", "content": analysis_prompt}
            ], temperature=temp)
            
            # Пытаемся распарсить JSON
            import json
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Ошибка при анализе настроения: {e}")
            # Возвращаем дефолтные значения
            return {
                "sentiment": "neutral",
                "interest_level": 5,
                "purchase_readiness": 5,
                "objections": [],
                "key_questions": [],
                "response_strategy": "continue_conversation"
            }
    
    async def generate_follow_up(
        self, 
        conversation_history: List[Dict[str, str]], 
        analysis: Dict[str, Any]
    ) -> str:
        """
        Генерирует персонализированное продолжение разговора
        
        Args:
            conversation_history: История разговора
            analysis: Результат анализа последнего сообщения
        
        Returns:
            Персонализированный ответ
        """
        strategy_prompt = f"""
        На основе анализа сообщения клиента:
        - Настроение: {analysis['sentiment']}
        - Уровень заинтересованности: {analysis['interest_level']}/10
        - Готовность к покупке: {analysis['purchase_readiness']}/10
        - Возражения: {analysis['objections']}
        - Стратегия: {analysis['response_strategy']}
        
        Сгенерируй персонализированный ответ, который:
        1. Учитывает текущее настроение клиента
        2. Отвечает на его ключевые вопросы и возражения
        3. Мягко направляет к следующему этапу воронки продаж
        4. Сохраняет доверительный тон общения
        """
        
        messages = conversation_history + [
            {"role": "system", "content": strategy_prompt}
        ]
        
        # Для творческих задач используем более высокую температуру если поддерживается
        temp = 0.8 if not self.is_gpt5 else None
        
        return await self.get_completion(messages, temperature=temp)
    
    async def check_api_health(self) -> bool:
        """Проверяет доступность OpenAI API"""
        try:
            params = self._get_completion_params(max_tokens=10)
            params["messages"] = [{"role": "user", "content": "Привет"}]
            
            response = await self.client.chat.completions.create(**params)
            return True
        except Exception as e:
            logger.error(f"OpenAI API недоступен: {e}")
            return False
    
    def estimate_tokens(self, text: str) -> int:
        """Более точная оценка количества токенов в тексте"""
        # Для русского текста: примерно 2.5-3 символа на токен
        return int(len(text) / 2.5)
    
    async def get_available_models(self) -> List[str]:
        """Получает список доступных моделей"""
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data if 'gpt' in model.id.lower()]
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей: {e}")
            return []
        
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Распознает голосовое сообщение через Whisper API
        
        Args:
            audio_file_path: Путь к аудио файлу
            
        Returns:
            Распознанный текст
        """
        try:
            logger.info(f"🎤 Отправка аудио на распознавание: {audio_file_path}")
            
            with open(audio_file_path, 'rb') as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"  # Русский язык
                )
            
            text = transcript.text
            logger.info(f"✅ Распознано {len(text)} символов: '{text[:100]}...'")
            return text
            
        except Exception as e:
            logger.error(f"❌ Ошибка распознавания аудио: {e}")
            return ""