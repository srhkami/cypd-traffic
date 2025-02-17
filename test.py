from utils.options import get_options, get_person
from utils.log import log
from utils.webdriver import open_browser, fx
from utils.excel import load_excel, save_excel
from static.case import CaseReply
from selenium.webdriver.support.ui import Select


if __name__ == '__main__':
  undertakers = get_person()
  for u in undertakers.values():
    print(u.name)