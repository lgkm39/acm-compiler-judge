#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals

import StringIO
import codecs
import csv
import hashlib
import json
import os
import requests
import shutil
import sys
import time
from collections import namedtuple
from datetime import datetime
from jinja2 import Environment, PackageLoader, select_autoescape, Template

import settings
import utils
from database import db_session, init_db
from models import *


def download():
    for i in range(1, 365):
        url = 'https://acm.sjtu.edu.cn/compiler2017/download/testcase_' + str(i) + '.txt'
        r = requests.get(url)

        with open('./docs/testcases/T' + str(i) + '.mx', 'wb') as file:
            file.write(r.content)


def clear_testcase():
    db_session.query(TestRun).delete()
    db_session.query(Testcase).delete()
    db_session.commit()


def clear_all():
    db_session.query(TestRun).delete()
    db_session.query(BuildLog).delete()
    for c in db_session.query(Compiler):
        c.latest_version_id = None
    db_session.commit()
    db_session.query(Version).delete()
    db_session.commit()


def add_testcase():
    add_list = '364 363 362 361 360 357 353 352 351 350 349 348 345 344 340 338 337 335 334 333 331 330 329 328 327 326 325 324 321 313 297 296 295 293 292 289 288 287 286 284 282 279 277 274 272 265 259 258 257 255 253 248 247 243 241 240 238 236 235 234 233 232 231 230 229 227 226 225 224 223 222 221 220 219 218 217 215 213 212 211 210 209 208 207 206 205 204 202 201 200 199 197 196 195 194 193 192 190 189 188 187 185 184 183 181 180 178 177 176 174 172 170 169 168 167 166 165 164 158 157 156 148 146 143 141 140 138 136 134 133 132 131 130 129 127 124 123 122 121 120 119 118 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34 33 32 31 30 29 28 27 26 25 23 22 21 20 19 18 17 16 15 14 13 11 9 7 3 2 1'.split()
    print(add_list)
    for i in add_list:
        with codecs.open('./docs/testcases/T' + str(i) + '.mx', 'r', 'utf-8') as f:
            content = f.read()
        t = utils.parse_testcase(content)
        testcase = Testcase(enabled=True,
                            phase=t['phase'],
                            is_public=t['is_public'],
                            comment=t['comment'],
                            timeout=t.get('timeout', None),
                            cnt_run=0,
                            cnt_hack=0,
                            content=json.dumps(t))
        db_session.add(testcase)
    db_session.commit()

if __name__ == '__main__':
    pass
    # clear_all()
    # clear_testcase()
    # add_testcase()

# # -*- coding: utf-8 -*-
# import urllib
# import time
# import json
# class Basic:
#     def __init__(self):
#         self.__accessToken = ''
#         self.__leftTime = 0
#     def __real_get_access_token(self):
#         appId = "wx8288ac4f89bdf492"
#         appSecret = "d38f386d71559d64f5127e8e5b164556"
#         postUrl = ("https://api.weixin.qq.com/cgi-bin/token?grant_type="
#                    "client_credential&appid=%s&secret=%s" % (appId, appSecret))
#         urlResp = urllib.urlopen(postUrl)
#         urlResp = json.loads(urlResp.read())
#         self.__accessToken = urlResp['access_token']
#         self.__leftTime = urlResp['expires_in']
#
#     def get_access_token(self):
#         if self.__leftTime < 10:
#             self.__real_get_access_token()
#             return self.__accessToken
#
#     def run(self):
#         while(True):
#             if self.__leftTime > 10:
#                 time.sleep(2)
#                 self.__leftTime -= 2
#             else:
#                 self.__real_get_access_token()