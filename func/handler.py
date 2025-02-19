import time
import requests
from utils.log import log
from utils.options import select_undertaker, Undertaker
from utils.excel import load_excel, save_excel
from utils.webdriver import open_browser, get_intranet_headers
from func.get import get_case_detail
from static.case import Case



