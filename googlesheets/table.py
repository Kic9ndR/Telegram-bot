from typing import List, Union, Dict
import pygsheets


class GoogleTable:
    """Класс для работы с Google Sheet."""
    def __init__(
        self, credence_service_file:str = "creds.json", googlesheet_file_url:str = "https://docs.google.com/spreadsheets/d/111DoQAlShuGQITdTBxwxFs1SLMcWPU0_6Q3pAjSdB0c"
    ) -> None:
        """Инициализирует класс.
        Args:
            credence_service_file (str): Путь до сервисного файла credence.json (Google Sheet API).
            googlesheet_file_url (str): Ссылка на Google Sheet.
        Returns:
        """
        self.credence_service_file = credence_service_file
        self.googlesheet_file_url = googlesheet_file_url

    def _get_googlesheet_by_url(
        self, googlesheet_client: pygsheets.client.Client
    ) -> pygsheets.Spreadsheet:
        """Получает Google.Docs таблицу по ссылке на документ."""

        sheets: pygsheets.Spreadsheet = googlesheet_client.open_by_url(
            self.googlesheet_file_url
        )
        return sheets.sheet1

    def _get_googlesheet_client(self):
        """Авторизуется с помощью сервисного ключа и 
        возвращает клиентский объект Google Docs.
        """
        return pygsheets.authorize(
            service_file=self.credence_service_file
        )

    def search_abonement(
        self,
        data: List[List[Union[str, bool]]],
        id_worker: int = 1,
        status_work: int = 4,
        link_work: int = 5
    ) -> Union[List[str],int]:
        """Возвращает информацию из определнных столбоцв таблицы (куда записаны абонементы).
        Args:
            data (List[List[Union[str, bool]]]): Данные для поиска в таблице.
            id_worker (int): Диапазон поиска по столбцам.
        Returns (List[str]|int): Возвращает список c данных столбцов
        """
        googlesheet_client: pygsheets.client.Client = self._get_googlesheet_client()
        wks: pygsheets.Spreadsheet = self._get_googlesheet_by_url(googlesheet_client)
        try:
            find_cell = wks.find(data, matchEntireCell=True, cols=(id_worker, id_worker))[0]
        except:
            return -1
        find_cell_row = find_cell.row
        status = wks.get_value((find_cell_row, status_work))
        link = wks.get_value((find_cell_row, link_work))
        return [status, link]
