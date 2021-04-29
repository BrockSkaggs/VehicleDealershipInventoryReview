#Ref. Beautiful Soup: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
import datetime as dt
import json
import re

from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options 

from dealer_inventory_db_util import DealerVehicleDbUtil
from models.dealer_vehicle import DealerVehicle

driver_path = 'chromedriver.exe'
num_regex = re.compile('^\d+$')
price_regex = re.compile(r'\$[0-9]+,[0-9]+')
db_util = DealerVehicleDbUtil()

def main():
    print('Running...')

    chrome_options=Options()
    # chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
    scan_time = dt.datetime.now()

    fletcher_ford_vehicles = read_common_ford(driver, scan_time, "https://www.frankfletcherford.net/used-inventory/index.htm?start=", "Frank Fletcher Ford")
    carthage_ford_vehicles = read_common_ford(driver, scan_time, "https://www.carthageford.net/used-inventory/index.htm?start=", "Carthage Ford")
    max_motor_vehicles = read_max_motors(driver, scan_time)
    griffith_motor_vehicles = read_griffith_motor(driver, scan_time)
    carthage_cdjr_vehicles = read_carthage_cdjr(driver, scan_time)
    mike_carpino_vehicles = read_common_ford(driver, scan_time, "https://www.mikecarpinofordlincoln.com/used-inventory/index.htm?start=", "Mike Carpino Ford") 

    #TODO: 
    # 1. Create GitHub repository to hold project details.
    # 2. www.mayse.com has similar website to Max Motors --- Attempt to share code to scrape both websites.

    vehicles = fletcher_ford_vehicles + carthage_ford_vehicles + max_motor_vehicles + griffith_motor_vehicles + carthage_cdjr_vehicles + \
        mike_carpino_vehicles
    driver = None

    db_util.store_vehicles(vehicles)
    print('Completed.')

def scrape_common_ford(html: str, scan_time: dt.datetime, dealer: str) -> []:
    soup = BeautifulSoup(html, 'html.parser')
    vehicle_detail_containers = soup.find_all('div', {'class': "vehicle-card-details-container"})

    vehicles = []

    for v_container in vehicle_detail_containers:
        v_desc = v_container.find('h2').text
        cond_desc = v_desc[5:].strip()
        year = int(v_desc[0:4])
        engine = v_container.find('li', {'class':'engine'}).text if v_container.find('li', {'class':'engine'}) is not None else None
        transmission = v_container.find('li', { 'class':'transmission'}).text if v_container.find('li', { 'class':'transmission'}) is not None else None
        mpg = v_container.find('li', { 'class':'cityMpg'}).text if v_container.find('li', { 'class':'cityMpg'}) is not None else None
        stockNumber = v_container.find('li', {'class':'stockNumber'}).text
        vin = v_container.find('li', {'class':'vin'}).text

        odometer = None
        odometer_element = v_container.find('li', {'class': 'odometer'})
        if odometer_element is not None:
            raw_odo = odometer_element.text
            cond_odo = raw_odo.replace('miles','').replace(',','').strip()
            odometer = int(cond_odo) if num_regex.match(cond_odo) is not None else odometer_element.text

        price = None
        price_element = v_container.find('span', {'class':'price-value'})
        if price_element is not None:
            raw_price = price_element.text
            cond_price = raw_price.replace('$','').replace(',','').strip()
            price = int(cond_price) if num_regex.match(cond_price) is not None else price_element.text

        if dealer == "Carthage Ford":
            desc_price_matches = price_regex.findall(v_desc)
            if len(desc_price_matches) == 1:
                price = int(desc_price_matches[0].replace('$','').replace(',','')) 

        vehicle = db_util.build_dealer_vehicle(dealer, cond_desc, year, engine, transmission, odometer, mpg, stockNumber, vin,
            price, scan_time)

        vehicles.append(vehicle)

    return vehicles

def read_common_ford(driver, scan_time: dt.datetime, url_stem: str, dealer: str) -> []:
    start_val = 1
    qty_discovered = 99
    v_dets = []
    i=1
    while qty_discovered > 0:
        url = url_stem + str(start_val)
        print(f"Scraping URL: {url}")
        driver.get(url)
        page_v_dets = scrape_common_ford(driver.page_source, scan_time, dealer)
        qty_discovered = len(page_v_dets)
        v_dets.extend(page_v_dets)
        start_val=18*i+1
        i += 1

    return v_dets

def read_max_motors(driver, scan_time: dt.datetime) -> []:
    page = 1
    limit = 100
    offset = 0
    qty_discovered = 99
    v_dets = []

    while qty_discovered > 0:
        url = f"https://www.maxmotors71.com/VehicleSearchResults?search=preowned&limit={limit}&offset={offset}&page={page}"
        print(f"Scraping URL: {url}")
        driver.get(url)
        page_v_dets = scrape_max_motors(driver.page_source, scan_time)
        v_dets.extend(page_v_dets)
        qty_discovered = len(page_v_dets)
        page += 1
        offset += limit
    
    return v_dets

def scrape_max_motors(html: str, scan_time: dt.datetime) -> []:
    soup = BeautifulSoup(html, 'html.parser')
    vehicles = []
    containers = soup.find_all('section')
    containers = [c for c in containers if 'id' in c.attrs.keys() and c.attrs['id'].startswith('card-view')]

    cnt = 0
    for container in containers:
        if not 'data-params' in container.attrs.keys():
            continue
        data_params = container.attrs['data-params']
        if not 'bodyType' in data_params:
            continue

        raw_desc = container.find('h4').text.replace('\n',' ').replace('Pre-Owned', '').strip()
        year = int(raw_desc[0:4])
        desc = raw_desc[5:].strip()

        #Price
        price_div = container.find('div', {'itemprop': 'priceSpecification'})
        price = None
        for span in price_div.find_all('span', {'class':'value big-and-bold'}):
            if span.text.upper() == 'RETAIL PRICE':
                continue
            price_matches = price_regex.findall(span.text)
            price = int(price_matches[0].replace('$','').replace(',','')) if len(price_matches) == 1 else span.text

        specs_list = container.find('ul',{'class':'vehicleIdentitySpecs'})

        for list_item in specs_list.find_all('li'):
            if list_item.attrs['template'].endswith('stockNumber'):
                stock_num = list_item.find('span', {'class':'value'}).text
            elif list_item.attrs['template'].endswith('miles'):
                miles = int(list_item.find('span', {'class':'value'}).text.replace(',','')) 
            elif list_item.attrs['template'].endswith('engine'):
                engine = list_item.find('span', {'class':'value'}).text
            elif list_item.attrs['template'].endswith('transmission'):
                transmission = list_item.find('span', {'class':'value'}).text
            elif list_item.attrs['template'].endswith('vin'):
                vin = list_item.find('span', {'class':'value'}).text
        
        vehicle = db_util.build_dealer_vehicle('Max Motors', desc, year, engine, transmission, str(miles), None, 
            None, vin, price, scan_time)
        vehicles.append(vehicle)
        cnt += 1

    return vehicles

def read_griffith_motor(driver, scan_time: dt.datetime) -> []:
    page_index = 0
    qty_discovered = 99
    v_dets = []

    while qty_discovered > 0:
        url = f"https://www.griffithmotor.com/used-vehicles/?_p={page_index}&_dFR%5Btype%5D%5B0%5D=Used&_dFR%5Btype%5D%5B1%5D=Certified%2520Used&_paymentType=our_price"
        print(f"Scraping URL: {url}")
        driver.get(url)
        page_v_dets = scrape_griffith_motor(driver.page_source, scan_time)
        v_dets.extend(page_v_dets)
        qty_discovered = len(page_v_dets)
        page_index += 1
    
    return v_dets

def scrape_griffith_motor(html: str, scan_time: dt.datetime) -> []:
    soup = BeautifulSoup(html, 'html.parser')
    vehicles = []
    
    containers = soup.find_all('div', {'class':'result-wrap used-vehicle stat-image-link'})
    
    results_div = soup.find(id='hits')

    for card in results_div.children:
        if not 'data-vehicle' in card.attrs.keys():
            continue
        data_v_attribute = json.loads(card.attrs['data-vehicle']) 

        price = data_v_attribute['price']
        stock_num = data_v_attribute['stock']
        year = int(data_v_attribute['year']) 
        vin = data_v_attribute['vin']
        desc = f"{data_v_attribute['make']} {data_v_attribute['model']} {data_v_attribute['trim']}"

        miles_element = card.find('li', {'class':'vehicle-details--item mileage'})
        miles_text = miles_element.text if miles_element is not None else ''
        
        miles = None if miles_text == '' else int(miles_text.replace('Mileage:', '').replace(',','').strip())

        vehicle = db_util.build_dealer_vehicle('Griffith Motor', desc, year, None, None, str(miles), None, stock_num, vin, price,
            scan_time)
        vehicles.append(vehicle)

    return vehicles

def read_carthage_cdjr(driver, scan_time: dt.datetime) -> []:
    #Only reading certified pre-owned inventory - during development only 1 page of results was visible.
    url = "https://www.carthagecdjr.com/certified-inventory/index.htm"
    driver.get(url)
    v_dets =scrape_carthage_cdjr(driver.page_source, scan_time)
    return v_dets

def scrape_carthage_cdjr(html: str, scan_time: dt.datetime) -> []:
    soup = BeautifulSoup(html, 'html.parser')
    vehicles = []

    card_list = soup.find('ul', {'class':'vehicle-card-list list-unstyled transition-property-opacity transition-duration-sm transition-timing-function-standard'})

    for card in card_list.children:
        raw_desc = card.find('h2').text
        year = int(raw_desc[0:4])
        desc = raw_desc[5:]
        engine = card.find('li',{'class':'engine'}).text
        transmission = card.find('li',{'class':'transmission'}).text
        miles = int(card.find('li',{'class':'odometer'}).text.replace('miles', '').replace(',',''))
        mpg = card.find('li',{'class':'fuelEconomy'}).text
        stock_num = card.find('li',{'class':'stockNumber'}).text
        vin = card.find('li',{'class':'vin'}).text

        price_div = card.find('div',{'class':'vehicle-card-pricing w-100'})
        price = None
        if price_div is not None:
            price = int(price_div.find('span',{'class':'price-value'}).text.replace('$','').replace(',',''))

        vehicle = db_util.build_dealer_vehicle('Carthage CDJR', desc, year, engine, transmission, str(miles), mpg, 
            stock_num, vin, price, scan_time)
        vehicles.append(vehicle)
    return vehicles


if __name__ == '__main__':
    main()