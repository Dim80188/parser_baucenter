import asyncio 
from concurrent.futures import ProcessPoolExecutor 
from bs4 import BeautifulSoup 
import json 
import aiohttp 

# 1.собираем со страницы каталога ссылки на категории
# 2.собираем со страниц с категориями ссылки на страницы со списком товаров
# 3.заходим на страницу с товаром и собираем данные по товарам

async def make_request(url, session):
    response = await session.get(url)
    if response.ok:
        return response
    else:
        print(f'{url} returned: {response.status}')

def _get_html_container(html):
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
    return links[:2]

def _get_html_container_2(html):
    soup = BeautifulSoup(html, 'lxml')
    container = soup.find('div', class_='ib-wrapper catalog catalog-product-list')
    container_1 = container.find('aside', class_='catalog-sidebar hidden-xs')
    links = []
    rows = container_1.find_all('article', class_='catalog-sidebar_item')
    for row in rows:
        links_1 = row.find('div', class_='catalog-sidebar_item_body').find('ul', class_='catalog-sidebar_item_body--visible').find_all('li')
        for i in links_1:
            link = i.find('a').get('href')
            link = 'https://baucenter.ru' + link
            # print(f'Добавляю {link}')
            links.append(link)
        try:
            links_2 = row.find('div', class_='catalog-sidebar_item_body').find('ul', class_='catalog-sidebar_item_body--hidden').find_all('li')
            for i in links_2:
                link = i.find('a').get('href')
                link = 'https://baucenter.ru' + link
                # print(f'Добавляю {link}')
                links.append(link)
        except:
            pass          
    return links

def _get_data(html):
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
            
            

        with open('result_async.json', 'w') as file:
            json.dump(result, file, indent=4, ensure_ascii=False)

async def get_first_step(first_step_queue, session):
    url = 'https://baucenter.ru/catalog/'
    response = await make_request(url, session)
    html = await response.text()
    # синхронный код из асинхронной функции вызываем только передав его в отдельный поток(процесс)
    # получаем текущий событийный цикл
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        # запускаем синхронную функцию в отдельном процессе
        first_step_links = await loop.run_in_executor(
            pool, _get_html_container, html 
        )
        
    # помещаем ссылку в очередь
    for link in first_step_links:
        await first_step_queue.put(link)
    return first_step_queue


async def get_second_step(first_step_queue, second_step_queue, session):
    # while True:
    url = await first_step_queue.get()
    response = await make_request(url, session)
    html = await response.text()
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor() as pool:
        second_step_links = await loop.run_in_executor(
            pool, _get_html_container_2, html
        )
    first_step_queue.task_done()
    for link in second_step_links:
        await second_step_queue.put(link)
    return second_step_queue

async def get_data_step(second_step_queue, session):
    while True:
        url = await second_step_queue.get()
        response = await make_request(url, session)
        html = await response.text()
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor() as pool:
            await loop.run_in_executor(
                pool, _get_data, html
            ) 
        second_step_queue.task_done() 

async def main():
    session = aiohttp.ClientSession()
    # создаем экземпляр очереди
    first_step_queue = asyncio.Queue()
    second_step_queue = asyncio.Queue()
    # создаем список для новых задач
    page_getters = []
    task = asyncio.create_task(get_first_step(first_step_queue, session))
    page_getters.append(task)

    page_2_getters = []
    for i in range(2):
        task = asyncio.create_task(
            get_second_step(first_step_queue, second_step_queue, session)
        )
        page_2_getters.append(task)

    data_getters = []
    for i in range(4):
        task = asyncio.create_task(
            get_data_step(second_step_queue, session)
        )
        data_getters.append(task)
    
    await asyncio.gather(*page_getters)
    await first_step_queue.join()
    await second_step_queue.join()
    for task in page_getters:
        task.cancel()
    for task in data_getters:
        task.cancel()

    await session.close()

asyncio.run(main())