import pygsheets

class GoogleTable:
    def __init__(
        self, 
        credence_service_file:str = "creds.json", 
        googlesheet_file_url:str = "https://docs.google.com/spreadsheets/d/1NQrStv45dgDhxkvkBrYvJfr2wfW3xBVDMqPZO44xQ3g"
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


    def create_sheet(self, title: str):                                                 # Создаю лист пользователя
        googlesheet_client = self._get_googlesheet_client()
        sheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        src_worksheet = sheet.worksheet_by_title('Scheme')
        return sheet.add_worksheet(title=title, rows=20, cols=10, src_worksheet=src_worksheet)
    

    def add_name(self, name: str, username: str):                                       # Добавление имени
        googlesheet_client = self._get_googlesheet_client()
        sheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        worksheet = sheet.worksheet_by_title(name)
        value = f'https://t.me/{username}'
        add_name = worksheet.update_row(index=2, values=[name])
        add_username = worksheet.update_row(index=2, values=[value], col_offset=3)
        return add_name, add_username


    def update_status(self, title: str, work: str, new_status: str):                    # Обновляю статус работы
        googlesheet_client = self._get_googlesheet_client()
        sheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        worksheet = sheet.worksheet_by_title(title)
        for c in range(worksheet.rows):
            cell = f'A{c + 1}'
            work_name = worksheet.get_value(cell)
            if work in work_name:
                value = worksheet.get_value(f'G{c+1}')
                if new_status != 'Выполнено':
                    if value != '':
                        count = int(value) + 1
                    else:
                        count = 1
                status = worksheet.update_value(f'C{c+1}' , new_status)
                new_value = worksheet.update_value(f'G{c+1}', int(count))
                return status, new_value


    def add_user_work(self, name: str, data):                                    # Добавление работы сотруднику
        googlesheet_client = self._get_googlesheet_client()
        sheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        worksheet = sheet.worksheet_by_title(name)
        return worksheet.append_table(values=data, dimension='ROWS', overwrite=False)


    def add_user_info(                                                          # Добавляется информация о реквизитах, программах и городе сотрудника 
            self,
            title: str,
            payment_details: str,
            work_programs: str,
            residence_city: str,
            drive: str,
    ):
        googlesheet_client = self._get_googlesheet_client()
        sheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        worksheet = sheet.worksheet_by_title(title)
        payment = worksheet.update_value('H2', payment_details)
        programs = worksheet.update_value('I2', work_programs)
        city = worksheet.update_value('J2', residence_city)
        new_drive = worksheet.update_value('K2', drive)
        return payment, programs, city, new_drive


    def add_user_drive(
            self,
            title: str,
            drive: str,
    ):
        googlesheet_client = self._get_googlesheet_client()
        sheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        worksheet = sheet.worksheet_by_title(title)
        new_drive = worksheet.update_value('K2', drive)
        return new_drive


    def get_all_info(self, title: str):                                                 # Получаем всю информацию с листа в диапазоне data[-:-]
        googlesheet_client = self._get_googlesheet_client()
        sheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        worksheet = sheet.worksheet_by_title(title)                                     # Название листа
        data = worksheet.get_all_values()                                               # Диапазон чтения с листа
        return [row[6] for row in data[0:]]
    
    
    def get_link_worker(self, title: str):                                              # Ссылка на лист сотрудника
        googlesheet_client = self._get_googlesheet_client()
        sheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        worksheet = sheet.worksheet_by_title(title)
        url = "https://docs.google.com/spreadsheets/d/"+ str(sheet.id) +"/edit#gid="+ str(worksheet.id)
        return url
    

    def add_project(                                                     # Добавляется проект в график проектов
        self,
        project_name: str,
        curator: str,
        start_date,
        end_date,
        comment: str,
    ):
        googlesheet_client = self._get_googlesheet_client()
        sheet = googlesheet_client.open_by_url(self.googlesheet_file_url)
        worksheet = sheet[0]
        for c in range(worksheet.rows):         # Значение строки, начинается с 0
            value = worksheet.get_value(f'B{c+1}')
            if value == '' and c != 0:
                project_title = worksheet.update_value(f'B{c+1}', project_name)
                project_curator = worksheet.update_value(f'C{c+1}', curator)
                project_start_date = worksheet.update_value(f'D{c+1}', start_date)
                project_end_date = worksheet.update_value(f'E{c+1}', end_date)
                project_comment = worksheet.update_value(f'B{c+2}', comment)
                return project_title, project_curator, project_start_date, project_end_date, project_comment