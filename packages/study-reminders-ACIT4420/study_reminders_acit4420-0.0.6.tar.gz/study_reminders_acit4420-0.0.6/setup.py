# setup . py
#from distutils.core import setup
# distutils is deprecated as of python 3.12, https://stackoverflow.com/questions/77233855/why-did-i-get-an-error-modulenotfounderror-no-module-named-distutils

# refer to https://packaging.python.org/en/latest/discussions/setup-py-deprecated/ for completing the package related portions of assignment

setup ( name = 'study_reminders' ,
version = '0.5' ,
author = 'Matthew Stanford' ,
author_email = 'masta6127@oslomet.no' ,
url = ' ' ,
packages =[ ' projectname ' , ' projectname . utils', 'schedule'] ,
)