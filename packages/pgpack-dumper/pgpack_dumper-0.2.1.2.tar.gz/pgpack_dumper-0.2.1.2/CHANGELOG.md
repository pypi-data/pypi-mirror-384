# Version History

## 0.2.1.2

* Add dbname.sql & gpversion.sql to queryes directory
* Add PGPackDumper.dbname attribute to detect greenplum or postgres
* Change PGPackDumper.version to "version number|greenplum version number" if greenplum detected

## 0.2.1.1

* Add wheels automake
* Update depends pgpack==0.3.0.8

## 0.2.1.0

* Add *.pyi files for cython module descriptions
* Update MANIFEST.in
* Update depends pgpack==0.3.0.7
* Update depends setuptools==80.9.0

## 0.2.0.7

* Update depends pgpack==0.3.0.6
* Add depends psycopg_binary>=3.2.10
* Add internal methods __read_dump, __write_between and __to_reader to force kwargs creation

## 0.2.0.6

* Add tell() method to CopyReader
* Update requirements.txt depends pgpack==0.3.0.5

## 0.2.0.5

* Delete attribute pos from CopyBuffer
* Add readed and sending size output into log

## 0.2.0.4

* Update requirements.txt depends pgpack==0.3.0.4
* Update requirements.txt depends psycopg==3.2.10
* Fix logger create folder in initialize

## 0.2.0.3

* Change log message
* Improve refresh database after write
* Improve initialization error
* Rename variable result to output

## 0.2.0.2

* Update MANIFEST.in
* Update requirements.txt depends pgpack==0.3.0.3
* Improve pyproject.toml license file approve
* Add CHANGELOG.md to pip package
* Add close files after read/write operations
* Change log messages for read operations

## 0.2.0.1

* Update requirements.txt depends pgpack==0.3.0.2
* Fix multiquery decorator
* Fix pgpack import

## 0.2.0.0

* Redistribute project directories
* Add CopyReader class for read stream
* Add StreamReader class for read same as PGPack stream object
* Add new method to_reader(query, table_name) for get StreamReader
* Add new method from_rows(dtype_data, table_name) for write from python iterable object
* Add new methods from_pandas(data_frame, table_name) & from_polars(data_frame, table_name)
* Add new methods refresh() to refresh session & close() to close PGPackDumper
* Update requirements.txt
* Update README.md
* Change default compressor to ZSTD
* Change CopyBuffer.copy_reader() function
* Delete CopyBuffer read() & tell() functions
* Delete make_buffer_obj method

## 0.1.2.2

* Hotfix root_dir() function

## 0.1.2.1

* Add array nested into metadata
* Add attribute version
* Add more error classes
* Update requirements.txt
* Change initialized message to log
* Change multiquery log

## 0.1.2

* Change metadata structure
* Update requirements.txt

## 0.1.1

* Rename project to pgpack_dumper
* Fix legacy setup.py bdist_wheel mechanism, which will be removed in a future version
* Fix multiquery
* Add CHANGELOG.md

## 0.1.0

* Add CopyBufferObjectError & CopyBufferTableNotDefined
* Add PGObject
* Add logger
* Add sqlparse for cut comments from query
* Add multiquery
* Update requirements.txt

## 0.0.2

* Fix include *.sql
* Fix requirements.txt
* Docs change README.md

## 0.0.1

First version of the library pgcrypt_dumper
