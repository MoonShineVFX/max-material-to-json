'''
Created on 2020-6-9

@author: noflame.lin
'''

import pymxs
rt = pymxs.runtime
import max_utils
reload(max_utils)

from max_utils import set_parent


def dcc_file_name():
    return max_utils.maxfilename()


def dcc_export_folder():
    return max_utils.export_folder()


def export_abc(filename):
    max_utils.export_abc(filename)


def export_mapping_table(filename):
    max_utils.export_table(filename)


def export_mat(filename):
    max_utils.export_mat(filename)
