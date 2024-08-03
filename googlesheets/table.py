import pygsheets

class GoogleTable:
    def __init__(
        self, 
        credence_service_file:str = "creds.json", 
        googlesheet_file_url:str = "https://docs.google.com/spreadsheets/d/111DoQAlShuGQITdTBxwxFs1SLMcWPU0_6Q3pAjSdB0c"
    ) -> None:

        self.credence_service_file = credence_service_file
        self.googlesheet_file_url = googlesheet_file_url

    def _get_googlesheet_by_url(self, googlesheet_client):
        """Получает Google.Docs таблицу по ссылке на документ."""

        sheets = googlesheet_client.open_by_url(self.googlesheet_file_url)
        return sheets.sheet1

    def _get_googlesheet_client(self):
        """Авторизуется с помощью сервисного ключа и 
        возвращает клиентский объект Google Docs.
        """
        return pygsheets.authorize(
            service_file=self.credence_service_file
        )

    def get_second_column(self):
        googlesheet_client = self._get_googlesheet_client()
        sheets = googlesheet_client.open_by_url(self.googlesheet_file_url)
        sheet1 = sheets.sheet1
        data = sheet1.get_all_values()
        return [row[1] for row in data[1:]]