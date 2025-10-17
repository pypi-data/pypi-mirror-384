from configparser import ConfigParser
import sys


class Config:
    def __init__(self, fileName):
        #print('Module: {}, {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.fileName = fileName
        if len(self.sections) == 1:
            self.credentials = 0

    @property
    def credentials(self):
        #print('Module: {}, {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        parser = ConfigParser(empty_lines_in_values=False)
        parser.read(self.fileName)
        sections = parser.sections()
        sect = sections[self.sec_no]
        params = dict(parser.items(sect))
        return params

    @credentials.setter
    def credentials(self, sec_no):
        #print('Module: {}, {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        self.sec_no = sec_no

    @property
    def sections(self):
        #print('Module: {}, {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        parser = ConfigParser(empty_lines_in_values=False)
        parser.read(self.fileName)
        sections = parser.sections()
        return sections

    @property
    def db_type(self):
        #print('Module: {}, {}, Class: {}, Def: {}'.format(__name__, __class__, sys._getframe().f_code.co_name))
        parser = ConfigParser(empty_lines_in_values=False)
        parser.read(self.fileName)
        sections = parser.sections()
        type = sections[self.sec_no].split('_')[0]
        return type
