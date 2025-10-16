import ast
import os.path
import re

from setuptools import find_packages, setup


NAME = 'rdfobj'
DESCRIPTION = 'A python library for object to triple mapping using OWL'
URL = 'https://forge.inrae.fr/pegase/rdfobject'
EMAIL = 'francois.moreews@inrae.fr'
AUTHOR = 'FJR Moreews'
REQUIRES_PYTHON = '>=3.8.10'
#REQUIRES_PYTHON = '>=3.9.7'





# What packages are required for this module to be executed?
REQUIRED = [
  'numpy>= 1.23.2','pandas>=1.4.4' ,'lxml>=4.9.1',
  'rdflib==6.2.0','graphviz==0.20.1', 'owlready2==0.39',
  'networkx>=2.8.8','Jinja2>=3.1.2','xsdata==22.11','rdfextras==0.4',
  'typepy==1.3.0','SPARQLWrapper==2.0.0',
  'jupyter==1.0.0','pydot==1.4.2','dill>=0.3.5.1',
  'matplotlib>=3.6.3'
]
  #'matplotlib>=3.6.3'
  #'matplotlib>=3.8.0'

# What packages are optional?
EXTRAS = {
  'testing': ["pytest"]
}

def findVersion(pkname,srcfile):
 
    vers="0.0.0" 

    reg = re.compile(r'__version__\s*=\s*(.+)')
    with open(os.path.join(pkname, srcfile)) as f:
 
      for line in f:
        print(line) 
        m = reg.match(line)
        if m:
            vers = ast.literal_eval(m.group(1))
 
            break
    return vers


ldescription=open('README.md').read()

setup(
   name=NAME,
   version=findVersion(NAME, '__init__.py'),
   description=DESCRIPTION,
   long_description=ldescription,
   long_description_content_type='text/markdown',
   author=AUTHOR,
   author_email=EMAIL,
   url=URL,
#   packages=[NAME],
   packages=find_packages(exclude=['tests']),
   license='MIT',
   platforms="Posix; MacOS X;",
   classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ],
   zip_safe=False,
   package_dir={NAME:NAME}, #important 
   package_data={
      NAME: [
             
              'resources/*', NAME+'/resources/*',
              'data/*', NAME+'/data/*'
            ]
   },
   python_requires=REQUIRES_PYTHON,
   install_requires=REQUIRED,
   extras_require=EXTRAS,
)

 


 
