import os
import pathlib
from distutils.core import setup

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(name='sintef-pyshop',
      version=os.getenv('CI_COMMIT_TAG'),
      author='SINTEF Energy Research',
      description='Python interface to SHOP',
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages=['pyshop',
                'pyshop.helpers',
                'pyshop.shopcore',
                'pyshop.lp_model'],
      package_dir={'pyshop': 'pyshop',
                   'pyshop.helpers': 'pyshop/helpers',
                   'pyshop.shopcore': 'pyshop/shopcore',
                   'pyshop.lp_model': 'pyshop/lp_model'},
      url='http://www.sintef.no/programvare/SHOP',
      project_urls={
          'Documentation': 'https://shop.sintef.energy/documentation/tutorials/pyshop/',
          'Source': 'https://gitlab.sintef.no/energy/shop/pyshop',
          'Tracker': 'https://shop.sintef.energy/tickets',
      },
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Education',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Programming Language :: Python :: 3.13',
      ],
      author_email='support.energy@sintef.no',
      license='MIT',
      python_requires='>=3.9',
      install_requires=['pandas', 'numpy', 'graphviz', 'packaging', 'requests'])
