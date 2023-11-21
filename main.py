import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sqlite3 as sql3
from sqlite3 import Error as Sql3err


def get_data_from_website_view(job_offers):
    job_items = driver.find_elements(By.CLASS_NAME, 'posting-list-item')

    for job_item in job_items:
        job_title = job_item.find_element(By.CLASS_NAME, 'posting-title__position')
        job_salary = job_item.find_element(By.CLASS_NAME, 'salary').text. \
            replace('PLN', '').replace(' ', '').split('–')

        if len(job_salary) == 2:
            job_salary = int(job_salary[0]) + int(job_salary[1]) // 2
        else:
            job_salary = int(job_salary[0])

        job_offer_temp = {'Job Title': job_title.text,
                          'Average salary': job_salary,
                          'Job Offer Website': job_item.get_attribute('href')}
        job_offers.append(job_offer_temp)


options = Options()
options.add_argument("-headless")

mode = input('Choose mode (headless/visible): ')
job_keyword = input('Enter your keyword: ')
print('Please wait for a result...')

job_offers = []

if mode == 'visible':
    driver = webdriver.Firefox()
else:
    driver = webdriver.Firefox(options=options)

driver.get('https://nofluffjobs.com/pl')
driver.switch_to.window(driver.window_handles[0])
WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))).click()
time.sleep(1)
WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/"
                                                                      "mat-dialog-container/div/div/div/div[2]/"
                                                                      "div[1]/div[1]/button"))).click()
WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[2]/div/'
                                                                      'mat-dialog-container/div/div/div/div[2]'
                                                                      '/div[2]/button[2]'))).click()
inputBox = driver.find_element(By.XPATH, '//*[@id="mat-chip-list-input-0"]')
inputBox.send_keys(job_keyword)
WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/nfj-root/nfj-layout/div[2]/div'
                                                                      '/div/div/nfj-search-box/form/mat-form-field'
                                                                      '/div/div[1]/div[1]/mat-chip-list/div'
                                                                      '/div[1]/button'))).click()

# more offers - scenario 1
while True:
    try:
        time.sleep(1)
        show_more_offers_button = driver.find_element(By.XPATH, '//button[normalize-space()="Zobacz więcej ofert"]')
        show_more_offers_button.click()
    except Exception:
        break

# more offers - scenario 2
while True:
    try:
        time.sleep(1)
        get_data_from_website_view(job_offers)
        next_page_button = driver.find_element(By.CSS_SELECTOR, "[aria-label='Next']")
        next_page_button.click()
    except Exception:
        break

print(f'Found {len(job_offers)} job offers!')
show_chart = input('Do you want to see salary chart? (YES/NO): ')

if show_chart == 'YES':
    salary_data = []

    for job_offer in job_offers:
        salary_data.append(job_offer['Average salary'])

    # creating the bar plot
    fig = plt.figure()
    plt.hist(np.array(salary_data), edgecolor='black', bins=max(salary_data) // 500)
    plt.xlabel("Salary levels")
    plt.ylabel("No. of job offers")
    plt.title("No. of job offers based on salary levels")
    plt.show()

save_mode = input('Please choose a way to save the data (XLSX/SQLITE): ')

if save_mode == 'SQLITE':
    conn = None
    try:
        conn = sql3.connect('job.db')
        print('Connected successfully with job.db!')

        conn.execute('''CREATE TABLE IF NOT EXISTS OFFERS (
                OFFER_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                JOB_TITLE TEXT NOT NULL,
                AVERAGE_SALARY INTEGER NOT NULL,
                JOB_OFFER_URL TEXT);''')

        for job_offer in job_offers:
            conn.execute('''INSERT INTO OFFERS (JOB_TITLE, AVERAGE_SALARY, JOB_OFFER_URL) 
                                    VALUES (?, ?, ?)''',
                         (job_offer['Job Title'], job_offer['Average salary'], job_offer['Job Offer Website']))

        conn.commit()
    except Sql3err as e:
        print(e)
    finally:
        if conn:
            conn.close()
else:
    job_offers_df = pd.DataFrame(job_offers, columns=['Job Title', 'Average salary', 'Job Offer Website'])
    excel_writer = pd.ExcelWriter('jobOffers.xlsx', engine='openpyxl')
    job_offers_df.to_excel(excel_writer, index=False, sheet_name='Sheet1')
    workbook = excel_writer.book
    worksheet = excel_writer.sheets['Sheet1']

    # Adjust column widths to fit the content
    for idx, col in enumerate(job_offers_df):
        max_length = max(job_offers_df[col].astype(str).map(len).max(), len(col))
        worksheet.column_dimensions[worksheet.cell(row=1, column=idx + 1).column_letter].width = max_length + 2

    workbook.save('jobOffers.xlsx')
    excel_writer.close()

print('Saved succesfully!')
input("Press Enter to close the browser window...")
driver.close()
