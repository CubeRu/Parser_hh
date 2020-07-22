import os
import time
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup as Bs
from pandas import ExcelWriter as Xl


def parser(url):
    """Подключаемся, парсим, чистим и сортируем данные"""
    headers = {'accept': '*/*',
               'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                         ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}
    # Регулярное выражение, которое используется в качестве фильтра найденных вакансий
    stop_vacancy = r'(\w+(лодн)\w+|\w+(влеч)\w+|\w\D(ll)[^\']|\w(олл)[^\']|\w*(даж)|\w+(ДАЖ)\w|\w+(елефо)\w|' \
                   r'\w+(аркет)\w+|(звон)\w+|\w+(ктно)\w[^\']|\w+(sell)|\w*(одящ)\w*|\w*(одав)\w*|' \
                   r'\w*([s|S]ale)(\b|\w)[^f]|\w*([К|к][Л|л][И|и][Е|е])\W)'
    jobs_lst = []
    pagination_url = [url]
    session = requests.Session()
    request = session.get(url, headers=headers, timeout=5)
    if request.status_code == 200:
        print(f'Сервер ответил со статусом {str(request.status_code)}!', end='', flush=True)
        time.sleep(.8)
        print('\rПоиск вакансий', end='', flush=True)
        soup = Bs(request.content, 'lxml')
        # Находим ссылки на страницы в пагинации
        try:
            pagination = soup.find_all('a', attrs={'data-qa': 'pager-page'})
            count = int(pagination[-1].text)
            for i in range(count):
                p_url = url + f'&page={i}'
                if p_url not in pagination_url:
                    pagination_url.append(p_url)
        except TypeError:
            pass
        # Проходимся по списку страниц пагинации
        for p_url in pagination_url:
            request = session.get(p_url, headers=headers, timeout=5)
            soup = Bs(request.content, 'lxml')
            divs = soup.find_all('div', attrs={'data-qa': 'vacancy-serp__vacancy'})
            # Пока парсятся данные, отображаем псевдоанимацию в строке
            for x in ['.'] * 3 + ['\b \b'] * 3:
                time.sleep(.3)
                print(x, end='', flush=True)
            # Парсим данные с каждой страницы пагинации
            for div in divs:
                title = div.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-title'}).text
                title_href = div.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-title'})['href']
                location = div.find('span', attrs={'data-qa': 'vacancy-serp__vacancy-address'}).text
                company = div.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'})
                # Если отсутствуют какаие-либо данные
                try:
                    if company is not None:
                        company = company.text
                    else:
                        raise TypeError
                except TypeError:
                    company = 'Компания не указана'
                responsibility = div.find('div',
                                          attrs={'data-qa': 'vacancy-serp__vacancy_snippet_responsibility'}).text
                if responsibility == '':
                    responsibility = 'Отсутствует описание вакансии'
                requirements = div.find('div',
                                        attrs={'data-qa': 'vacancy-serp__vacancy_snippet_requirement'}).text
                if requirements == '':
                    requirements = 'Отсутствует описание требований к вакансии'
                salary = div.find('span',
                                  attrs={'data-qa': 'vacancy-serp__vacancy-compensation'})
                try:
                    if salary is not None:
                        salary = salary.text
                    else:
                        raise TypeError
                except TypeError:
                    salary = 'З/П не указана'
                # Добавляем в список полученные данные
                jobs_lst.append({'name': title,
                                 'location': location,
                                 'company': company,
                                 'responsibility': responsibility,
                                 'requirements': requirements,
                                 'salary': salary,
                                 'name_href': title_href})
        print(f"\rНайдено {str(len(jobs_lst))} вакансий!")
        # Фильтрация полученного списка по регулярному выражению
        question = str(input('Будем фильтровать данные (да/нет)?: ')).strip().upper()
        if question == 'ДА':
            remove_vacancy = [x for x in jobs_lst if not re.findall(stop_vacancy, x['title'])]
            print(f'\rУдалили не нужное и получили {str(len(remove_vacancy))} вакансий!')
        else:
            remove_vacancy = jobs_lst
            print(f'\rОставили все как есть и получили {str(len(remove_vacancy))} вакансий!')
        finish_vacancy = sorted(remove_vacancy, key=lambda a: a['title'])
        return finish_vacancy
    else:
        print(f"Сервер ответил со статусом {str(request.status_code)} :(\nЧто-то пошло не так!"
              f"\nПопробуйте позже")


def files_writer(finish_vacancy, name, where):
    """Записываем все данные в файл Excel"""
    f_name = f'Вакансии по запросу - ({name}) в ({where}), (Количество - {str(len(finish_vacancy))}), ' \
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
    for vacancy in finish_vacancy:
        data = {columns[0]: vacancy['name'],
                columns[1]: vacancy['company'],
                columns[2]: vacancy['responsibility'],
                columns[3]: vacancy['requirements'],
                columns[4]: vacancy['location'],
                columns[5]: vacancy['salary'],
                columns[6]: vacancy['name_href']}
        data_array = data_array.append(pd.Series(data), ignore_index=True)
    data_array = data_array.reindex(columns=columns)
    data_array.to_excel(file, f'{time.strftime("%d-%m-%y_%H-%M-%S")}', index=False)
    file.save()
    print(f'Все, что собрали, записали в файл с названием: {f_name}')


def place(name):
    """Место поиска вакансий"""
    destination = {'НСК': 4,
                   'МСК': 1,
                   'СПБ': 2,
                   'ЕКБ': 3,
                   'Н.О': 1202,
                   'РФ': 113,
                   'БР': 16}
    where = str(input(f'Где ищем ({", ".join([key for key in destination]).lower()})?: ')).upper().strip()
    if where in destination:
        d = destination[where]
        url = f'https://hh.ru/search/vacancy?area={d}&st=searchVacancy&text={name}'
        return url, files_writer(parser(url), name, where)
    else:
        print(f'Я пока не знаю такого города \"{where}\"\nПопробуй ещё раз')
        return place(name)


def start_search():
    """Название вакансии"""
    name = input('Название вакансии: ').strip()
    return place(name)


start_search()
