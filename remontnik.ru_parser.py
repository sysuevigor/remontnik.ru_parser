import json
import re
import os
import random
import time
import urllib
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, unquote, urlunparse
from urllib.parse import urlparse, parse_qs
import requests
import validators
from bs4 import BeautifulSoup
from transliterate import translit
from typing import Union, List
from PIL import Image

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

phone_set = set()
data_dict = dict()
error_link = []


def get_links_page(url: str, headers: dict = None) -> Union[List[str], bool]:
    """
    Получение ссылок на страницы объявлений.
    :param url: Ссылка на страницу категории.
    :param headers: Заголовки для запросов.
    :return: Список ссылок на страницы объявлений или False, если страница не найдена.
    """
    links = []
    page = 1
    while True:
        try:
            # Загрузка страницы
            rs = requests.get(url, headers=headers, timeout=5)
            # print(rs.status_code)  # добавляем эту строку для проверки
            soup = BeautifulSoup(rs.text, 'html.parser')
            # Обработка страницы
            if rs.status_code == 200:
                print(f'\r  - Получение ссылок: {rs.url}', end="")
                board = soup.find('div', class_='portfolio-grid')
                for item in board.find_all('a'):
                    link = item.get('href')
                    if not link.startswith('https://www.remontnik.ru'):
                        link = 'https://www.remontnik.ru' + link
                        # print(link)
                    links.append(link)
            else:
                return False

            # Поиск ссылки на следующую страницу
            next_page = soup.find('a', {'class': 'next-page'})
            if next_page:
                # Если ссылка на следующую страницу найдена, обновляем url и продолжаем работу
                page += 1
                url = f"{url.split('?')[0]}?page={page}&{url.split('?')[1]}"
                url_parts = list(urlparse(url))
                query_dict = parse_qs(url_parts[4])
                query_dict['page'] = [str(page)]
                url_parts[4] = urllib.parse.urlencode(query_dict, doseq=True)
                url = urlunparse(url_parts)
            else:
                # Если ссылка на следующую страницу не найдена, значит это последняя страница и выходим из цикла
                break

        except Exception:
            continue

    return links if links else False



def get_phone(links: str, url: str, num: int):
    """
    Получение основных данных о пользователе разместившем объявление.
    :param link: Ссылка на страницу объявления.
    :param num: Номер ссылки в списке.
    """
    time.sleep(random.randrange(1, 4))
    try:
        rs = requests.get(url=links, headers=headers, timeout=7)
        if rs.status_code == 200:
            contact = BeautifulSoup(rs.text, 'lxml').find('div', class_="portfolio-detail")
            portfolio_id = url.split("/")[-2]
            parsed_url = urlparse(url)
            query_dict = parse_qs(parsed_url.query)
            category_id = query_dict.get('category_id', [''])[0]
            name = contact.find('h1').text
            name_photos = contact.find('span', {'itemprop': 'name'})
            terms_and_scope = contact.find('div', class_='portfolio-detail__info').find_all('div')[0].find('p').text.strip()
            list_of_works = contact.find('div', class_='portfolio-detail__info').find_all('div')[2].find('p').text.strip()
            average_price = contact.find('div', class_='portfolio-detail__info').find_all('div')[1].find('p').text.strip()
            additionally = contact.find('div', class_='portfolio-detail__info').find_all('div')[3].find('p').text.strip()
            user_name = contact.find('div', class_='contractor-block__name').find('a').text.strip()
            user_link = 'https://www.remontnik.ru' + contact.find('div', class_='contractor-block__name').find('a')['href']
            executor_id = re.findall(r'/(\d+)/$', user_link)[0]


            if name_photos is not None:
                name_photo = translit(name_photos.text, 'ru', reversed=True)
            result = int(portfolio_id) + 4321

            photo_links = []  # список ссылок на фото
            if not os.path.exists("Remontnik-foto"):
                os.mkdir("Remontnik-foto")

            for i, photo_url in enumerate(photo_links):
                # отправляем запрос на получение фото
                response = requests.get(photo_url)

                # сохраняем фото в папку с нумерацией
                with open(f"Remontnik-foto/{name_photo}_{result}_{i + 1:02d}.jpg", "wb") as f:
                    f.write(response.content)

                # получаем размеры фото
                with Image.open(f"Remontnik-foto/{name_photo}_{result}_{i + 1:02d}.jpg") as img:
                    width, height = img.size

                    # обновляем переменные для минимальных и максимальных размеров
                    if i == 0:
                        min_width, max_width, min_height, max_height = width, width, height, height
                    else:
                        if width < min_width:
                            min_width = width
                        elif width > max_width:
                            max_width = width
                        if height < min_height:
                            min_height = height
                        elif height > max_height:
                            max_height = height

            # Список всех файлов
            folder_path = 'Remontnik-foto'

            for filename in os.listdir(folder_path):
                filepath = os.path.join(folder_path, filename)
                print(filepath)

            resp = requests.get(url=user_link, headers=headers, timeout=7)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'lxml').find('div', class_="portfolio-detail")
                city = soup.find('div', class_='region').text.strip()
                area = soup.find('div', class_='text-muted').text.strip()
                portfolio_link = soup.find('a', href=re.compile(r'/catalog/master/\d+/portfolio/'))
                if portfolio_link is not None:
                    portfolio_text = portfolio_link.find('span', {'class': None}).text
                    foto_rabot = re.search(r'\((\d+)\)', portfolio_text).group(1)
                else:
                    foto_rabot = None

            else:
                if portfolio_id not in phone_set:
                    data_dict.update({f"{portfolio_id}": {
                        "category_id": category_id,
                        "name": name,
                        'name_photos': name_photos,
                        'filepath': filepath,
                        'photo_links': photo_links,
                        'min_width': min_width,
                        'min_height': min_height,
                        'max_width': max_width,
                        'max_height': max_height,
                        'terms_and_scope': terms_and_scope,
                        'list_of_works': list_of_works,
                        'average_price': average_price,
                        'additionally': additionally,
                        'executor_id': executor_id,
                        'user_name': user_name,
                        'city': None,
                        'area': None,
                        'foto_rabot': None
                    }
                    })
                phone_set.add(portfolio_id)
            print(f"  - {num + 1} | Данные получены: {portfolio_id} | {links}")

    except Exception as ex:
        print(f"  - {num+1} | Данные не получены: {links} {ex}")
        error_link.append(links)
        return


def thread_run(links: list):
    """
    Итерация по списку ссылок и запуск потоков для парсинга страниц объявлений.
    :param links: Список со ссылками на страницы объявлений.
    """
    with ThreadPoolExecutor(max_workers=5) as executor:
        temp = []
        for num, link in enumerate(links):
            temp.append([num, link])
            if len(temp) >= 5:
                for x in temp:
                    n = x[0]
                    ln = x[1]
                    executor.submit(get_phone, link=ln, num=n)
                temp.clear()
        if len(temp) < 5:
            for x in temp:
                n = x[0]
                ln = x[1]
                executor.submit(get_phone, link=ln, num=n)
            temp.clear()


def main():
    # Пример ссылки на страницу категории: https://www.bazar.club/jobsinusa
    """
    Запуск парсинга данных со страниц объявлений.
    """
    url = input("Введите ссылку на страницу категории: ")
    if validators.url(url):
         if links := get_links_page(url):
            print(f'\nНайдено ссылок на страницы товаров: {len(links)}')
            thread_run(links)
            if data_dict:
                with open(f'bazar_phone_{url.split("/")[-2]}.json', 'w', encoding='utf-8') as file:
                    json.dump(data_dict, file, indent=4, ensure_ascii=False)
                print(f"\nПолучено номеров: {len(data_dict)}\nДанные сохранены: "
                      f"bazar_phone_{url.split('/')[-2]}.json")
            else:
                print("\nНе удалось получить данные")
            if error_link:
                with open(f'bazar_phone_{url.split("/")[-2]}_error.txt', 'w', encoding='utf-8') as text:
                    for txt in error_link:
                        text.write(f'{txt}\n')
                print(f"\nОшибок: {len(error_link)}.\nДанные об ошибках сохранены: "
                      f"bazar_phone_{url.split('/')[-2]}_error.txt'")
         else:
            print("\nСсылок не найдено. Ошибка получения данных")

    else:
        print("Введенная ссылка не прошла валидацию. Проверьте правильность ввода")


if __name__ == "__main__":
    main()

