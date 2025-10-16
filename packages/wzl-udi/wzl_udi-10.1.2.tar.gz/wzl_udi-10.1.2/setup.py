from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(name='wzl-udi',
      version='10.1.2',
      url='https://git-ce.rwth-aachen.de/wzl-mq-public/soil/python',
      project_urls={
          "Bug Tracker": "https://git-ce.rwth-aachen.de/wzl-mq-public/soil/python/-/issues",
      },
      author='Matthias Bodenbenner',
      author_email='m.bodenbenner@wzl-mq.rwth-aachen.de',
      description='Provides REST-server, publisher-interface and serializer for the Unified Device Interface in Python based on the SensOr Interfacing Language (SOIL).',
      package_dir={'wzl': 'src'},
      packages=['wzl.http', 'wzl.soil', 'wzl.utils', 'wzl.stream'],
      long_description=long_description,
      long_description_content_type="text/markdown",
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
      ],
      install_requires=['aiohttp~=3.13.0',
                        'Deprecated~=1.2.13',
                        'nest-asyncio~=1.5.6',
                        'pytz==2024.1',
                        'wzl-mqtt~=2.6.1',
                        'rdflib~=7.0.0'
                        ],
      zip_safe=False)
