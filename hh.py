import os
import time
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup as Bs
from pandas import ExcelWriter as Xl

stop_vacancy = r'(\w(ll)\D|\w\D(ll)[^\']|\D\w(олл)\D|\D\w+(даж)|' \
               r'\D\w+(фо)\w\D|\w(аркето)\w|\D(звон)\w\D|\w+\D(ктного)\D?)'

headers = {'accept': '*/*',
           'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit'
                         '/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}

destination = {'НСК': 4,
               'РФ': 113}


def parser(url, headers):
    """Подключаемся, парсим, сортируем и чистим данные"""
    jobs_lst = []
    pagination_url = [url]
    session = requests.Session()
    request = session.get(url, headers=headers, timeout=5)
    if request.status_code == 200:
        print(f'Сервер ответил со статусом {str(request.status_code)}!')
        soup = Bs(request.content, 'html.parser')
        # Находим ссылки пагинации
        try:
            pagination = soup.find_all('a', attrs={'data-qa': 'pager-page'})
            count = int(pagination[-1].text)
            for i in range(count):
                p_url = url + f'&page={i}'
                if p_url not in pagination_url:
                    pagination_url.append(p_url)
        except:
            pass
        # Проходимся по списку страниц
        for p_url in pagination_url:
            request = session.get(p_url, headers=headers, timeout=5)
            soup = Bs(request.content, 'html.parser')
            divs = soup.find_all('div', attrs={'data-qa': 'vacancy-serp__vacancy'})
            # Парсим данные с каждой страницы
            for div in divs:
                title = div.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-title'}).text
                title_href = div.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-title'})['href']
                location = div.find('span', attrs={'data-qa': 'vacancy-serp__vacancy-address'}).text
                company = div.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'})
                # Если отсутствует название компании
                try:
                    if company is not None:
                        company = company.text
                    else:
                        raise TypeError
                except TypeError:
                    company = 'Компания не указана'
                responsibility = div.find('div',
                                          attrs={'data-qa': 'vacancy-serp__vacancy_snippet_responsibility'}).text
                requirements = div.find('div',
                                        attrs={'data-qa': 'vacancy-serp__vacancy_snippet_requirement'}).text
                salary = div.find('span',
                                  attrs={'data-qa': 'vacancy-serp__vacancy-compensation'})
                # Если отсутствует з/п
                try:
                    if salary is not None:
                        salary = salary.text
                    else:
                        raise TypeError
                except TypeError:
                    salary = 'З/П не указана'
                # Добавляем в список полученные данные
                jobs_lst.append({'title': title,
                                 'location': location,
                                 'company': company,
                                 'responsibility': responsibility,
                                 'requirements': requirements,
                                 'salary': salary,
                                 'title_href': title_href})
        # Сортируем данные по названию
        sort_vacancy = sorted(jobs_lst, key=lambda x: x['title'])
        print(f"Найдено {str(len(sort_vacancy))} вакансий!")
        # Проходимся по отсортированным данным и избавляемся от ысякой шляпы
        result = [x for x in sort_vacancy if not re.findall(stop_vacancy, x['title'])]
        print(f'Удалили не нужное и получили {str(len(result))} вакансий!')
        return result
    else:
        print(f"Сервер ответил со статусом {str(request.status_code)} :(\nНас палят Джек!"
              f"\nЛибо используй VPN, либо попробуй позже")


def files_writer(result, name):
    """Записываем все данные в файл Excel"""
    f_name = f'Вакансии по запросу - ({name}), (Количество - {str(len(result))}), ' \
             f'на ({time.strftime("%d-%m-%y_%H-%M-%S")}).xlsx'
    directory = os.path.join('C:/Users/unlim/OneDrive/Рабочий стол/Вакансии')
    # Если не использовать движок - xlsxwriter, то ссылки будут не кликабельны
    file = Xl(os.path.join(directory, f_name), engine='xlsxwriter')
    data_array = pd.DataFrame()
    columns = ['Название вакансии',
               'Компания',
               'Описание',
               'Требования',
               'Местоположение',
               'З/П',
               'Ссылка на вакансию']
    for vacancy in result:
        data = {columns[0]: vacancy['title'],
                columns[1]: vacancy['company'],
                columns[2]: vacancy['responsibility'],
                columns[3]: vacancy['requirements'],
                columns[4]: vacancy['location'],
                columns[5]: vacancy['salary'],
                columns[6]: vacancy['title_href']}
        data_array = data_array.append(pd.Series(data), ignore_index=True)
    data_array = data_array.reindex(columns=columns)
    data_array.to_excel(file, f'{time.strftime("%d-%m-%y_%H-%M-%S")}', index=False)
    file.save()
    print(f'Все, что спарсили, записали в файл с названием: {f_name}')


def place(name):
    """Место поиска вакансий"""
    where = str(input('Где ищем?: ')).upper()
    if where in destination:
        d = destination[where]
        url = f'https://hh.ru/search/vacancy?area={d}&st=searchVacancy&text={name}'
        jobs_lst = parser(url, headers)
        return jobs_lst, files_writer(jobs_lst, name)
    else:
        print(f'Я пока не знаю такого города \"{where}\"\nПопробуй ещё раз')
        return place(name)


def start_search():
    """Название вакансии"""
    name = str(input('Название вакансии: '))
    return place(name)


start_search()
