##  Copyright (c) 2018 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##


from setuptools import setup


setup(
    name = 'csv_metadata'
    ,version = '0.5.0'
    ,description = 'CSV Metadata Encoding tools'
    ,url = 'http://github.com/Upstream-Research/csv_metadata_encoding'
    ,author = 'Upstream Research, Inc.'
    ,author_email = ''
    ,license = 'MIT'
    ,keywords = 'csv metadata meta'
    ,classifiers = [
        'Development Status :: 3 - Alpha'
        ,'Environment :: Console'
        ,'License :: OSI Approved :: MIT License'
        ,'Programming Language :: Python'
        ,'Programming Language :: Python :: 3.5'
        ]
    ,packages = [ 
        'csv_metadata' 
        ]
    ,entry_points = {
        'console_scripts': [
             'csv-mkmeta = csv_metadata.csv_mkmeta:console_main'
            ,'csv-meta2csvt = csv_metadata.csv_meta2csvt:console_main'
            ]
        }
    ,long_description = '''
    Python tools to support CSV Metadata Encoding format.
    '''
    )
