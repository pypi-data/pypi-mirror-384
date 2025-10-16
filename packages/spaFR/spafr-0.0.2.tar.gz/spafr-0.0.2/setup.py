from setuptools import setup
from setuptools import find_packages

setup( name = 'spaFR',
version = '0.0.2',
description='Deciphering cellular resolution functional redundancy from transcriptomic data',
url='https://github.com/wangjingwan/SpaFR/tree/master#',
author='Jingwan WANG',
author_email='wanwang6-c@my.cityu.edu.hk',
license='MIT',
packages=find_packages(),
install_requires = [
        'pandas==1.5.3',
        'numpy==1.24.4',
        'seaborn==0.11.2',
        'matplotlib==3.8.4',
        'tqdm==4.67.1',
        'statannot==0.2.3',
        'scipy==1.9.3',
        'networkx==3.2.1',
        'statsmodels==0.14.5',
        'scikit-learn==1.6.1'
],
package_data={'pathway': ['*.txt']},
include_package_data=True
)
