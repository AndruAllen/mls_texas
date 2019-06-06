from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
import pandas as pd
import time
from bs4 import BeautifulSoup

HOUSE_ATTRIBUTES = ['mls_number', 'list_office', 'list_agent', 'transaction_type', 'zip', 'county', 'full_addr',
                    'monies_required', 'list_price', 'deposit', 'application_fee', 'HOA', 'original_list_price', 'restrictions',
                    'fenced_yard', 'pets_allowed', 'num_pets_allowed', 'pet_deposit', 'non_refundable_pet_fee', 'pet_rent',
                    'master_bedroom', 'kitchen', 'living_room', 'num_living_rms', 'num_dining_rms', 'num_stories',
                    'bedrooms', 'baths', 'year_built', 'sq_ft', 'acres', 'date_available', 'energy_saving_features',
                    'summary', 'interior_features', 'exterior_features', 'appliances', 'other_equipment', 'tenant_pays',
                    'construction_materials', 'flooring', 'house_style', 'housing_type', 'parking_features', 'heating']

COLLIN_COUNTY_ZIPS = ['75189', '75409', '75024', '75023', '75025', '75034', '75072', '75035', '75407', '75424', '75009', # collin county
                      '75442', '75454', '75069', '75071', '75070', '75075', '75074', '75078', '75252', '75093', '75013',
                      '75097', '75094', '75485', '75098', '75287', '75121', '75033', '75164', '75002', '75166', '75173',
                      '75010', '75036', '75056', # the colony according to google?
                      '75068'] # denton county frisco according to google?

MLS_URL = 'https://michealstafford.matrix.ntreis.net/Matrix/Public/?L=1&ap=SCH#1'
MLS_URL_TROY = 'https://matrix.ntreis.net/Matrix/Public/Portal.aspx?L=1&k=2979695XDcDZ&p=ALL-0-0-H#1'
ZIP_INPUT_ID = 'Fm1083_Ctrl1755_TextBox'
UL_WITH_NUM_RESULTS_ID = '_ctl0_m_lblPagingSummary'
RETURN_BUTTON_ID = '_ctl0_m_btnClosePILP'

options = Options()
#options.headless = True
BROWSER = webdriver.Firefox(options=options)  # Single global browser
BROWSER.implicitly_wait(10)
BROWSER.get(MLS_URL)


def scrollDown():
  try:
    for i in range(500):
      elem = BROWSER.find_element_by_xpath(
          '//a[@href="javascript:PortalResultsJs.getNextDisplaySet();"]')
      elem.click()
  except:
    pass  # scroll until you can't


def getHomesAtZip(zip, lease=True):
  BROWSER.refresh()  # load the filter selector again
  # Select house type:
  house_type_elems = []
  if(lease):
    house_type_elems = BROWSER.find_elements_by_xpath(
        "//option[@title='LSE-House']")
  else:
    house_type_elems = BROWSER.find_elements_by_xpath(
        "//option[@title='RES-Single Family']")
  num_fnd = len(house_type_elems)
  if(num_fnd == 1):
    house_type_elems[0].click()
  else:
    raise Exception(
        'Should only find one element when selecting home type. Instead found {} elements'.format(num_fnd))
  # Select a given zip code:
  zip_element = BROWSER.find_element_by_id(ZIP_INPUT_ID)
  zip_element.send_keys(zip)
  zip_element.send_keys(Keys.RETURN)
  zip_element.send_keys(Keys.RETURN)
  time.sleep(5)
  scrollDown()


def loadDetailPage(index):
  xpath = ''
  if(type(index) == int):
    xpath = '//a[contains(@href, "javascript:__doPostBack(\'_ctl0$m_DisplayCore\',\'Redisplay|1219,,'
    xpath += str(index)
    xpath += '\')")]'
  else:
    xpath = '//a[@href="' + index + '"]'
  try:
    elem = BROWSER.find_element_by_xpath(xpath)
    elem.click()
  except Exception as e:
    print(str(e))
    print('Failed to find house at index:', index)


def returnToFilteredResults():
  try:
    elem = BROWSER.find_element_by_id(RETURN_BUTTON_ID)
    elem.click()
  except Exception as e:
    print(str(e))
    print('Failed to return')


'''def get_MLS_numbers(num_found, _zip):
  s = set()
  mls_numbers_in_order = []
  elems = BROWSER.find_elements_by_xpath('//span[@class="d-text d-fontSize--small d-fontWeight--bold"]')
  length = len(elems)
  try:
    for i in range(length): # to keep elements refreshed
      mls_numbers_in_order.append(int(elems[i].get_attribute('innerHTML')))
      s = s.union(set([mls_numbers_in_order[-1]]))
  except Exception as e:
    print('Failed to get MLS numbers')
    print(str(e))
    getHomesAtZip(_zip) # try again
    mls_numbers_in_order = -1
  if(num_found != length):
    print('Number of houses doesn\'t match:', length)
    getHomesAtZip(_zip) # try again
    return -1
  return mls_numbers_in_order'''


def get_addresses_MLSs_ids(num_found, _zip, lease=True):
  d = dict()
  addr_elems = BROWSER.find_elements_by_xpath(
      "//span[@class='formula J_formula']")  # class for each house box
  mls_elems = BROWSER.find_elements_by_xpath(
      '//span[@class="d-text d-fontSize--small d-fontWeight--bold"]')
  try:
    for i in range(len(mls_elems)):
      pieces = {'zip': _zip, 'lease': lease,
                'href': None, 'href_id': None, 'full_addr': None}
      # mls number
      mls_number = int(mls_elems[i].get_attribute('innerHTML'))
      j = i * 5
      # example: '<a href="javascript:__doPostBack(\'_ctl0$m_DisplayCore\',\'Redisplay|1219,,0\')">940 Dover Lane</a>'
      # should be embedded street address
      href_html = addr_elems[j + 3].get_attribute('innerHTML')
      href_split = href_html.split('">')
      # example: ' Murphy, Texas 75094-4248'
      city_addr = addr_elems[j + 4].get_attribute('innerHTML')
      # example: href.split('">')[-1] = 940 Dover Lane</a>
      street_addr = href_split[-1][:-4]
      pieces['full_addr'] = street_addr + city_addr
      # href used, guessed index
      # example: javascript:__doPostBack(\'_ctl0$m_DisplayCore\',\'Redisplay|1219,,0\')
      pieces['href'] = href_split[0][9:]
      pieces['href_id'] = int(href_split[0].split('Redisplay|1219,,')[-1][:-2])
      if mls_number not in d:
        d[mls_number] = pieces
      else:
        print(mls_number, 'same id:',
              pieces['href_id'] == d[mls_number]['href_id'])
        print('Already seen')
  except Exception as e:
    print(len(addr_elems), len(mls_elems))
    print(str(e))
    getHomesAtZip(_zip)  # try again
    return -1
  if(len(d.keys()) != num_found):
    print("num elems:", len(d.keys()), 'vs', num_found)
    getHomesAtZip(_zip)  # try again
    return -1
  return d


'''def get_addresses(num_found, _zip):
  s = set()
  addresses_in_order = []
  elems = BROWSER.find_elements_by_xpath("//span[@class='formula J_formula']") # class for each house box
  length = len(elems)
  try:
    for i in range(0,length,5): # to keep elements refreshed
      # example: '<a href="javascript:__doPostBack(\'_ctl0$m_DisplayCore\',\'Redisplay|1219,,0\')">940 Dover Lane</a>'
      street_addr = elems[i+3].get_attribute('innerHTML') # should be embedded street address
      # example: ' Murphy, Texas 75094-4248'
      city_addr = elems[i+4].get_attribute('innerHTML')
      #if(street_addr.find('href="javascript:') == -1): # sannity check
      #  print('possible error:',street_addr, city_addr)
      #else:
      street_addr = street_addr.split('\')">')[-1][:-4] # example: street_addr.split('\')">')[-1] = 940 Dover Lane</a>
      addresses_in_order.append(street_addr+city_addr)
      s = s.union(set([addresses_in_order[-1]]))
  except Exception as e:
    print('Failed to get addresses')
    print(str(e))
    getHomesAtZip(_zip) # try again
    addresses_in_order = -1

  if(len(s) != num_found):
    print("num elems:",len(s))
    getHomesAtZip(_zip) # try again
    return -1
  return addresses_in_order'''

'''
PARSE THE HTML
'''


def dataframeHTML():
  try:
    top_elem = BROWSER.find_element_by_xpath(
        '//div[@class="row d-bgcolor--systemLightest d-marginBottom--8 d-marginTop--6 d-paddingBottom--4"]')
    top_summary = BeautifulSoup(
        top_elem.get_attribute('innerHTML'), "html.parser")
    side_elem = BROWSER.find_element_by_xpath(
        '//div[@class="col-sm-6 d-bgcolor--systemLightest"]')
    side_div = BeautifulSoup(
        side_elem.get_attribute('innerHTML'), "html.parser")
  except Exception as e:
    print('Couldn\'t find top and/or side elements')
    print(str(e))
    return -1


'''
ITERATE THRU
'''


def iterateThruZIPs(lease=True):
  total_found = 0
  total_dict = dict()
  table = pd.DataFrame(columns=HOUSE_ATTRIBUTES)
  for _zip in COLLIN_COUNTY_ZIPS:
    print('Finding homes at', _zip, end=": ")
    getHomesAtZip(_zip, lease)  # True for leases
    num_found = 0
    try:
      check = BROWSER.find_element_by_id("_ctl0_m_pnlRenderedDisplay").get_attribute(
          "innerHTML").find("No matches found")
      if(check == -1):
        temp_element = BROWSER.find_element_by_id(UL_WITH_NUM_RESULTS_ID)
        # example: '<ul class="pager mtx-pager" style="padding-top: 10px;">\n <b>25</b> Total  results\n</ul>'
        temp_text = temp_element.get_attribute('innerHTML')
        # parsing text surrounding desired number
        find_num = temp_text.split('</b> Total  result')
        if(len(find_num) == 2):
          find_num = find_num[0].split('<b>')
          num_found = int(find_num[-1])
        else:
          print('Should be 2:', len(find_num))
          print(temp_text)
        print(num_found)
      else:
        print('None found')
    except:
      print('Too many found')
    stuff_per_zip, ind = -1, 0
    # change to be a set that can take in the appropriate index number + mls + addr to be able to visit and match
    while(stuff_per_zip == -1 and ind < 3):
      print('attempt', ind)
      stuff_per_zip = get_addresses_MLSs_ids(num_found, _zip, lease)
      ind += 1
    if(stuff_per_zip != -1):
      for key in stuff_per_zip.keys():
        if(key in total_dict):
          print(key, total_dict[key])
          print('is already here')
          print('trying to add', stuff_per_zip[key])
        else:
          total_dict[key] = stuff_per_zip[key]
          loadDetailPage(stuff_per_zip[key]['href'])

    # not necessarily unique
    total_found += num_found
  print('total seen:', total_found)
  return total_dict, total_found


#temp = BROWSER.find_element_by_id("_ctl0_m_pnlRenderedDisplay").get_attribute("innerHTML").find("No matches found")

# d-text d-fontSize--small d-fontWeight--bold
# href="javascript:__doPostBack(\'_ctl0$m_DisplayCore\',\'Redisplay|1219,,0\')"

#HOUSE_CLASS = "row d-paddingTop--6 d-paddingBottom--6 d-bgcolor--systemLightest d-marginBottom--4 d-marginLeft--4 d-marginRight--4 d-marginTop--0"
#<a href="javascript:__doPostBack(\'_ctl0$m_DisplayCore\',\'Redisplay|1219,,1')">4804 Nocona Drive</a>
#<a href="javascript:__doPostBack('_ctl0$m_DisplayCore','Redisplay|1219,,3')">4520 White Rock Lane</a>
