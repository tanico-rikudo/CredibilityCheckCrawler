# -*- coding: utf-8 -*-
import time,os,json,csv,gzip

# import screenshot_driver as sd #chrome用の独自プラグイン
import scroll as sc #scroll用の独自プラグイン
import crawl_setting as cs #myself用の設定プラグイン

from datetime import datetime as dt
import time

# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options #chrome
# from selenium.webdriver.common.action_chains import ActionChains

import pandas as pd
import hashlib #ハッシュ化
from numpy.random import *
from bs4 import BeautifulSoup as bs

import copy
import subprocess

import timeout_decorator
import requests
import shutil
import codecs
import urlparse
import Queue
from datetime import datetime as dt
import crawl_setting as cs #myself用の設定プラグイン
import agent as ag
import link_pool_st as lp
import access_pool as ap

import multiprocessing
from time import sleep
from datetime import datetime as dt
import datetime as dt_parent
import sys,os,shutil,csv
import random ### seed?urlをシャッフル（実装済み）＊＊＊＊説明無し＊＊＊＊

import crawl_setting as cs #myself用の設定プラグイン
import json