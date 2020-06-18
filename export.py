'''
Created on 2020-6-9

@author: noflame.lin
'''

import pymxs
rt = pymxs.runtime
import max_utils
reload(max_utils)


def export_abc(filename):
    max_utils.export_abc(filename)


def export_mapping_table(filename):
    max_utils.export_table(filename)


def export_mat(filename):
    max_utils.export_mat(filename)
