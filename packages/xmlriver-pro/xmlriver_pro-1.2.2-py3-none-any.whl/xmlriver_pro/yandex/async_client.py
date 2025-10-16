"""
Асинхронный клиент для Yandex Search API через XMLRiver
"""

from typing import Dict, Any, Optional, List

from ..core.async_base_client import AsyncBaseClient
from ..core.types import (
    SearchResponse,
    SearchResult,
    NewsResult,
    AdResult,
    OneBoxDocument,
    KnowledgeGraph,
    SearchType,
    TimeFilter,
    DeviceType,
    OSType,
    RelatedSearch,
)
from ..core.exceptions import ValidationError
from ..utils.validators import (
    validate_query,
    validate_device,
    validate_os,
)


class AsyncYandexClient(AsyncBaseClient):
    """
    Асинхронный клиент для Yandex Search API

    Поддерживает все типы поиска Yandex через XMLRiver API:
    - Органический поиск
    - Поиск новостей
    - Рекламные блоки
    - Специальные блоки (колдунщики)
    """

    BASE_URL = "https://xmlriver.com/search_yandex/xml"

    def __init__(
        self,
        user_id: int,
        api_key: str,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_retry: bool = True,
        session: Optional[Any] = None,
    ):
        """
        Инициализация асинхронного Yandex клиента

        Args:
            user_id: ID пользователя XMLRiver
            api_key: API ключ
            timeout: Таймаут запроса в секундах
            max_retries: Максимальное количество попыток повтора
            retry_delay: Базовая задержка между попытками в секундах
            enable_retry: Включить автоматические повторы
            session: Существующая aiohttp сессия
        """
        super().__init__(
            user_id=user_id,
            api_key=api_key,
            system="yandex",
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            enable_retry=enable_retry,
            session=session,
        )

    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.ORGANIC,
        num_results: int = 10,
        start: int = 0,
        device: DeviceType = DeviceType.DESKTOP,
        os: OSType = OSType.ANDROID,
        **kwargs,
    ) -> SearchResponse:
        """
        Асинхронный поиск в Yandex

        Args:
            query: Поисковый запрос
            search_type: Тип поиска (web, news)
            num_results: Количество результатов
            start: Начальная позиция
            device: Тип устройства
            os: Операционная система
            **kwargs: Дополнительные параметры

        Returns:
            SearchResponse: Результаты поиска
        """
        # Валидация параметров
        validate_query(query)
        validate_device(device)
        validate_os(os)

        if not 1 <= num_results <= 100:
            raise ValidationError(400, "num_results must be between 1 and 100")
        if start < 0:
            raise ValidationError(400, "start must be non-negative")

        # Параметры запроса
        params = {
            "query": query,
            "type": search_type.value,
            "num": num_results,
            "start": start,
            "device": device.value,
            "os": os.value,
            **kwargs,
        }

        return await self._make_request(self.BASE_URL, params, search_type.value)

    async def search_news(
        self,
        query: str,
        num_results: int = 10,
        start: int = 0,
        time_filter: Optional[TimeFilter] = None,
        **kwargs,
    ) -> SearchResponse:
        """
        Асинхронный поиск новостей в Yandex

        Args:
            query: Поисковый запрос
            num_results: Количество результатов
            start: Начальная позиция
            time_filter: Фильтр по времени
            **kwargs: Дополнительные параметры

        Returns:
            SearchResponse: Результаты поиска новостей
        """
        params = {
            "query": query,
            "type": "news",
            "num": num_results,
            "start": start,
            **kwargs,
        }

        if time_filter:
            params["time"] = time_filter.value

        return await self._make_request(self.BASE_URL, params, "news")

    async def get_ads(
        self, query: str, num_results: int = 10, **kwargs
    ) -> SearchResponse:
        """
        Асинхронное получение рекламных блоков Yandex

        Args:
            query: Поисковый запрос
            num_results: Количество результатов
            **kwargs: Дополнительные параметры

        Returns:
            SearchResponse: Рекламные блоки
        """
        params = {"query": query, "type": "ads", "num": num_results, **kwargs}

        return await self._make_request(self.BASE_URL, params, "ads")

    async def get_special_blocks(self, query: str, **kwargs) -> SearchResponse:
        """
        Асинхронное получение специальных блоков Yandex (колдунщики)

        Args:
            query: Поисковый запрос
            **kwargs: Дополнительные параметры

        Returns:
            SearchResponse: Специальные блоки
        """
        params = {"query": query, "type": "special", **kwargs}

        return await self._make_request(self.BASE_URL, params, "special")

    def _extract_results(
        self, data: Dict[str, Any], search_type: str
    ) -> List[SearchResult]:
        """Извлечение результатов из ответа Yandex API"""
        results = []

        # Извлекаем основные результаты
        if "results" in data and "result" in data["results"]:
            results_data = data["results"]["result"]
            if not isinstance(results_data, list):
                results_data = [results_data]

            for item in results_data:
                result = self._create_search_result(item, search_type)
                if result:
                    results.append(result)

        # Извлекаем специальные блоки Yandex
        if "special_blocks" in data:
            special_blocks = data["special_blocks"]
            if isinstance(special_blocks, dict):
                for block_type, block_data in special_blocks.items():
                    if block_type == "onebox" and isinstance(block_data, dict):
                        onebox = OneBoxDocument(
                            content_type="onebox",
                            title=block_data.get("title", ""),
                            url=block_data.get("url", ""),
                            snippet=block_data.get("snippet", ""),
                        )
                        results.append(onebox)

                    elif block_type == "knowledge_graph" and isinstance(
                        block_data, dict
                    ):
                        kg = KnowledgeGraph(
                            entity_name=block_data.get("title", ""),
                            description=block_data.get("description", ""),
                            image_url=block_data.get("image_url", ""),
                            additional_info=block_data.get("attributes", {}),
                        )
                        results.append(kg)

                    elif block_type == "related_searches" and isinstance(
                        block_data, list
                    ):
                        for related_item in block_data:
                            if isinstance(related_item, dict):
                                related = RelatedSearch(
                                    query=related_item.get("query", ""),
                                    url=related_item.get("url", ""),
                                )
                                results.append(related)

        return results

    def _create_search_result(
        self, item: Dict[str, Any], search_type: str
    ) -> Optional[SearchResult]:
        """Создание объекта результата поиска"""
        try:
            if search_type == "news":
                return NewsResult(
                    rank=int(item.get("position", 0)),
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    media=item.get("media"),
                    pub_date=item.get("pub_date"),
                )
            if search_type == "ads":
                return AdResult(
                    url=item.get("url", ""),
                    ads_url=item.get("ads_url", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                )
            # web
            return SearchResult(
                rank=int(item.get("position", 0)),
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
            )
        except (ValueError, KeyError) as _:
            # Логируем ошибку и возвращаем None
            return None
