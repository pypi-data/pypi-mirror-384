from setuptools import setup, find_packages

with open('README.md') as f:
    long_description = f.read()

setup(name='dgdb',
      version="1.0.0a0",
      description=f'Ver 1.0.0a0.',
      long_description=long_description,
      long_description_content_type='text/markdown',  # This is important!
      classifiers=[
                   # 'Development Status :: 5 - Production/Stable',
                   'Development Status :: 3 - Alpha',
                   'License :: OSI Approved :: MIT License',
                   'License :: OSI Approved :: Apache Software License',
                   'Programming Language :: Python :: 3',
                   "Operating System :: OS Independent",
                   ],
      keywords='',
      url='https://gitlab.com/gng-group/dgdb.git',
      author='Malanris',
      author_email='admin@malanris.ru',
      license='MIT',
      packages=find_packages(),
      install_requires=['sqlalchemy>=1.4.54', ],
      include_package_data=True,
      zip_safe=False)
