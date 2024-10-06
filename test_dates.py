from selenium import webdriver
from selenium.webdriver.common.by import By


def get_dates(coord): # format: [value, value] test_dates.get_dates(list(CITY.values())[0][1], list(CITY.values())[0][0])
    lat = coord[1]
    long = coord[0]

    options = webdriver.FirefoxOptions()
    options.add_argument("--headless") 
    driver = webdriver.Firefox(options=options)
    driver.get("https://landsat.usgs.gov/landsat_acq")
    driver.implicitly_wait(30)

    try: 
        acq_button = driver.find_element(By.ID, 'ui-id-3')
        convert_button = driver.find_element(By.ID, 'convert')

        acq_button.click()
    except Exception as e:
        if e:
            driver.implicitly_wait(30)
            acq_button = driver.find_element(By.ID, 'ui-id-3')
            convert_button = driver.find_element(By.ID, 'convert')
            acq_button.click()

    lat_box = driver.find_element(By.ID, 'thelat')
    long_box = driver.find_element(By.ID, 'thelong')

    lat_box.send_keys(lat)
    long_box.send_keys(long)    

    driver.implicitly_wait(10)

    convert_button.click()

    driver.implicitly_wait(30)

    table = driver.find_element(By.ID, 'convertTableRows')

    rows = table.find_elements(By.TAG_NAME, 'tr')

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')

        values = [cell.text for cell in cells]

    return values
