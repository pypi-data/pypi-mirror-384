import os
import pkgutil

pkg_dir = os.path.dirname(__file__)
subpackages = []
for (module_loader, name, ispkg) in pkgutil.iter_modules([pkg_dir]):
    if ispkg:
        subpackages.append(name)
        # print(name)

# print('subpackages', subpackages)

compName = os.getenv('COMPUTERNAME')
try:
    compName = os.getenv('COMPUTERNAME')
    if compName == 'DESKTOP-5HHINGF':
        ini_users = r"D:\Python\MySQL\users.ini"
        ini_chelt = r"D:\Python\MySQL\cheltuieli.ini"
        ini_masina = r"D:\Python\MySQL\masina.ini"
        ini_aeroclub = r"D:\Python\MySQL\aeroclub.ini"
        report_dir = r"D:\Python\MySQL\onlineanywhere\static"
    else:

        ini_users = r"C:\_Development\Diverse\pypi\cfgm.ini"
        # ini_chelt = r"C:\_Development\Diverse\pypi\cfgmRN.ini"
        ini_chelt = r"C:\_Development\Diverse\pypi\cfgm.ini"
        ini_masina = r"C:\_Development\Diverse\pypi\cfgm.ini"
        # ini_file = r"C:\_Development\Diverse\pypi\cfgmRN.ini"
        ini_aeroclub = r"C:\_Development\Diverse\pypi\cfgm.ini"
        report_dir = r"C:\_Development\Diverse\pypi\radu\masina\src\masina\static"
except:
    ini_users = '/home/radum/mysite/static/wdb.ini'

