from setuptools import setup

with open('README.md', encoding='utf-8') as f:
  long_description = f.read()

setup(
  name='constructional-diversity',
  version='0.0.1',
  description='This is a package with which users can analyze constructional diversity, constructional complexity, and verbal diversity.', 
  long_description=long_description, 
  long_description_content_type = 'text/markdown', 
  author='Haerim Hwang',
  author_email='yayhaerim@gmail.com',
  url='https://pypi.org/project/constructional-diversity', 
  license='MIT', 
  python_requires='>=3.9', 
  install_requires=["collections", "more_itertools", "spacy", "math", "numpy", "csv", "sys", "os", "glob", "pandas", "torch"], 
  packages=[], 
  package_data={'':['*']}, 
  keywords=[], 

)