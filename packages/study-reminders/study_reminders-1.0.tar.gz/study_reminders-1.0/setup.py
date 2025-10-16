# setup.py
from setuptools import setup

setup(name='study_reminders',
      version= '1.0',
      author='Bilal Sahli',
      author_email= 'bisah2204@oslomet.no',
      url= "https://github.com/bilal99-coder/study_reminder",
      description= "A simple student reminder app",
      install_requires=[
        'schedule',
        'importlib-metadata; python_version>"3.10"'
      ])