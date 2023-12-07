import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import json

HEADERS = {'User-Agent': UserAgent().random}
URLS_LIST = []

def get_response(session, url):
    r = session.get(url, headers=HEADERS)
    return r.text

def get_html_container(html):
    soup = BeautifulSoup(html, 'lxml')
    container = soup.find('div', class_='ib-wrapper catalog catalog-product-list')

    container_1 = container.find('div', class_='catalog-right').find('div', class_='categories_table')

    links = []

    rows = container_1.find_all('div', class_='categories_row')
    for j in rows:
        links_1 = j.find_all('a', class_='categories_row_item')
        for i in links_1:
            link = i.get('href')
            link = 'https://baucenter.ru' + link
            links.append(link)
    # for i in links:
    #     with open('links.txt', 'a') as file:
    #         file.write(i)

    # return links[:-1]
    return links[:2]

def get_html_container_2(html):
    soup = BeautifulSoup(html, 'lxml')
    container = soup.find('div', class_='ib-wrapper catalog catalog-product-list')

    container_1 = container.find('aside', class_='catalog-sidebar hidden-xs')
    

    links = []

    rows = container_1.find_all('article', class_='catalog-sidebar_item')
    
    for row in rows:
        links_1 = row.find('div', class_='catalog-sidebar_item_body').find('ul', class_='catalog-sidebar_item_body--visible').find_all('li')
        
        
        for i in links_1:
            link = i.find('a').get('href')
            time.sleep(0.5)
            link = 'https://baucenter.ru' + link
            print(f'Добавляю {link}')
            links.append(link)
        try:
            links_2 = row.find('div', class_='catalog-sidebar_item_body').find('ul', class_='catalog-sidebar_item_body--hidden').find_all('li')
            for i in links_2:
                
                link = i.find('a').get('href')
                time.sleep(0.5)
                link = 'https://baucenter.ru' + link
                print(f'Добавляю {link}')
                links.append(link)
        except:
            pass
                
    return links

def get_data(html):
    soup = BeautifulSoup(html, 'lxml')
    container = soup.find('div', class_='ib-wrapper catalog catalog-lvl2 catalog-product-list')
    container_1 = container.find('div', class_='catalog-right')

    rows = container_1.find_all('div', class_='catalog-grid')
    result = []
    for row in rows:
        data_points = row.find_all('div', class_='catalog_item with-tooltip')
        for point in data_points:
            name = point.get('data-name')
            print(f'Внес в файл {name}')
            article = point.get('data-article')
            price = point.get('data-price')
            
            result.append(
                {
                    'name': name,
                    'article': article,
                    'price': price
                }
            )
            
            time.sleep(0.5)

        with open('result.json', 'w') as file:
            json.dump(result, file, indent=4, ensure_ascii=False)




def main():
    s = requests.Session()
    response = get_response(s, 'https://baucenter.ru/catalog')
    links_list_1 = get_html_container(response)
    links_list_2 = []
    for link in links_list_1:
        response = get_response(s, link)
        output = get_html_container_2(response)
        links_list_2.extend(output)

    for link in links_list_2:
        response = get_response(s, link)
        get_data(response)

    

if __name__ == '__main__':
    main()



