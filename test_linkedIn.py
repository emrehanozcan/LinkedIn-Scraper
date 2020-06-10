import csv
from parsel import Selector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import os, random, sys, time
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options

options = Options()
options.headless = False

# preparing csv file to store parsing result later
writer = csv.writer(open('testLinkedIn.csv', 'w' ,encoding='utf-8', newline=""), delimiter=",") 
writer.writerow(['name', 'job_title', 'location', 'ln_url','connection' ,'total_experience','working'])

driver = webdriver.Chrome(chrome_options=options, executable_path ='driver/chromedriver.exe')

driver.get('https://www.linkedin.com/uas/login')

#enter your email and password
username_input = driver.find_element_by_name('session_key')
username_input.send_keys('E-MAİL')

password_input = driver.find_element_by_name('session_password')
password_input.send_keys('PASSWORD')

# click on the sign in button
# we're finding Sign in text button as it seems this element is seldom to be changed
driver.find_element_by_xpath('//button[text()="Oturum açın"]').click()


from selenium.webdriver.support import expected_conditions
driver.get('https://www.google.com/')

#type the features you want to find
search_input = driver.find_element_by_name('q')
search_input.send_keys('site:linkedin.com/in/ AND "AI Resident" AND "America"')

search_input.send_keys(Keys.RETURN)

# grab all linkedin profiles from first page at Google
profiles= []
while True:
    next_page_btn =driver.find_elements_by_xpath("//a[@id='pnnext']")
    if len(next_page_btn) <1:
        print("no more pages left")
        break
    else:
        urls = driver.find_elements_by_xpath("//*[@class='r']/a")
        for url in urls:
            profiles.append(url.get_attribute('href')) 
    #taking some people for testing
    if(len(profiles)>=20):  
        break

    element =WebDriverWait(driver,5).until(expected_conditions.element_to_be_clickable((By.ID,'pnnext')))
    driver.execute_script("return arguments[0].scrollIntoView();", element)
    element.click()
print(len(profiles))

# visit each profile in linkedin and grab detail we want to get
for profile in profiles :
    time.sleep(1)
    driver.get(profile)
    time.sleep(2)  
    sel = Selector(text=driver.page_source)
    time.sleep(1)  

    #Is there an account to check
    if(sel.xpath('//title/text()').extract_first() == "LinkedIn"):
        continue

    #checking out profile picture
    if(driver.find_element_by_xpath('//div[@class = "presence-entity pv-top-card__image presence-entity--size-9 ember-view"]/img').get_attribute("src").find('data:image/gif;') != -1):
        continue
        
    time.sleep(1) 
    fail = 0

    try:
        name = sel.xpath('//title/text()').extract_first().split(' | ')[0]
        job_title = sel.xpath('//*[@class="mt1 t-18 t-black t-normal break-words"]/text()').extract_first().strip().replace("\n", " ")
        location = sel.xpath('//*[@class="t-16 t-black t-normal inline-block"]/text()').extract_first().strip()
        ln_url = driver.current_url
        time.sleep(1)
        connection = driver.find_element_by_css_selector("div.flex-1.mr5 > ul.pv-top-card--list.pv-top-card--list-bullet.mt1 > li:nth-child(2) > span").text
        connection = int(''.join([n for n in connection if n.isdigit()]))

        while True:
            try:
                time.sleep(2)
                show_more = driver.find_element_by_xpath("//button[contains(@class,'pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link link-without-hover-state')]")
                show_more.click()
            except Exception as e:
                break

        time.sleep(2)
        src = driver.page_source
        soup = BeautifulSoup(src,'lxml')
        time.sleep(2)  
        exp_section = soup.find('section', {'id': 'experience-section'})
        time.sleep(2)    
        li_tags = exp_section .find_all('li',attrs={'class':'pv-entity__position-group-pager pv-profile-section__list-item ember-view'})
        time.sleep(1)

        total_exp=0
        exp=[]
        working_date=[]
        for i in range(len(li_tags)):
            time.sleep(1)
            try:
                time.sleep(1)
                exp.append(li_tags[i].find('div', attrs={'class':'pv-entity__company-summary-info'}).find('h4').find_all('span')[1].get_text())
                working_date.append(li_tags[i].find('ul',attrs={'class':'pv-entity__position-group mt2'}).find('li').find('h4', attrs={'class':'pv-entity__date-range t-14 t-black--light t-normal'}).find_all('span')[1].get_text())

            except:
                time.sleep(1)
                exp.append(li_tags[i].find('a').find('span', attrs={'class':'pv-entity__bullet-item-v2'}).get_text())
                working_date.append(li_tags[i].find('h4', attrs={'class':'pv-entity__date-range t-14 t-black--light t-normal'}).find_all('span')[1].get_text())
           
    except:
        print('failed \n')
        fail = 1

    #experience calculation
    for i in exp:
        if(i.find('less than a year') != -1):
            continue
        if(i.find('yrs') != -1 or i.find('yr') != -1):
            res = [int(i) for i in i.split() if i.isdigit()]
            total_exp = total_exp + 12*res[0]
            if(len(res) == 1):
                continue
            total_exp += res[1]
        elif(i.find('mos') != -1 or i.find('mo') != -1):
            res = [int(i) for i in i.split() if i.isdigit()]
            total_exp = total_exp + res[0]

    exp.clear()
    year = int(total_exp/12)
    moon = int(total_exp%12)
    if(moon == 0 and year == 0):
        total_experience = "0 year 0 moon"
    else:
        total_experience = str(year)+" year " + str(moon)+" moon"
        
    #working status
    flag=0
    for i in working_date:
        if(i.find('Present') != -1):
            flag=1
            working=True
            break  
    if(flag == 0):
        working=False

    # print to console for testing purpose
    if(fail == 0):
        print(name)
        print(job_title)
        print(location)
        print(ln_url)
        print(connection)
        print("Total experience ",total_experience)
        print("Working => ",working)
        print('\n')
        writer.writerow([name, job_title, location, ln_url, connection, total_experience, working])
        
driver.quit()