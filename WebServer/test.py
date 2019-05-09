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
    add_list = '509 523 524 525 527 528 529 531 532 533 534 538 539 541 542 543 544 552 553 555 556 558 559 560 562 563 564 565 566 567 568 569 570 571 572 573 574 575 576 577 578 579 580 581 582 583 584 585 586 587 588 590 591 592 593 594 596 597 598 599 600 601 602 603 604 605 606 607 608 609 610 611 612 613 614 615 616 617 618 619 620 621 622 623 624 625 626 628 629 630 631 632 633 634 635 636 637 638 639 641 642 643 644 645 646 647 652 656 667 668 671 672 675 676 677 678 680 683 684 685 686 687 688 689 690 692 693 694 695 696 697 700 701 710 714 717 720 721 722 723 724 725 726 727 728 729 730 731 732 733 734 735 736 737 739 740 742 743 744 750 751 752 754 755 756 759 761 762 763 766 771 772 775 776 777 779 780 781 786 787 788 791 794 795 796 797 798 799 800 801 804 805 806 807 808 809 810 811 812 813 814 815 818 819 820 822 823 824 825 826 827 828 829 830 834 835 836 837 838 839 840 841 842 843 844 845 867 871 872 873 876 879 887 889 891 900 901 902 908 915 921 923 925 926 938 939 940 941 943 945 946 947 948 950 951 952 953 954 955 956 957 958 959 961 1245 1309 '.split()
    print(add_list)
    for i in add_list:
        with codecs.open('./docs/testcases/testcase_' + str(i) + '.txt', 'r', 'utf-8') as f:
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
    # clear_all()
    # clear_testcase()
    add_testcase()

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
