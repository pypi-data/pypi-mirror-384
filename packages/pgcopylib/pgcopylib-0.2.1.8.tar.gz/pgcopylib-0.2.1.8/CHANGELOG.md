# Version History

## 0.2.1.8

* Add wheels automake
* Improve strings functions
* Small refactors

## 0.2.1.7

* Add *.pyi files for cython modules descriptions
* Change str and repr methods
* Refactor some code
* Update MANIFEST.in

## 0.2.1.6

* Fix PostgreSQLDtype polars compatible types
* Fix digits dtype convert
* Fix write_numeric function

## 0.2.1.5

* Update MANIFEST.in
* Improve pyproject.toml license file approve
* Add CHANGELOG.md to pip package
* Add close() method to PGCopyReader & PGCopyWriter
* Add tell() method to PGCopyReader

## 0.2.1.4

* Reafactor write_date function
* Add MANIFEST.in
* Add MIT License

## 0.2.1.3

* Fix write_timestamp function
* Improve pandas.Timestamp write errors for date & datetime write functions
* Add date to datetime & datetime to date convert

## 0.2.1.2

* Fix PostgreSQLDtype values

## 0.2.1.1

* Change read_functions & write_functions to postgres_dtype

## 0.2.1.0

* Refactor project
* Redistribute project directories
* Improve some functions

## 0.2.0.1

* Setup.py code refactor
* Some fixes
* Cast Py_ssize_t data types to Cython data types

## 0.2.0.0

* Full refactor project
* Rewrite code to Cython for more performance
* Change PGCopy to PGCopyReader
* Speed up converter functions
* PGCopyReader now have only read_row generator to read one row and to_rows generator to read all rows
* PGCopyWriter now have methods write_row, from_rows, write and tell. fileobj now is optional.

## 0.1.3

* Rename PGCopyWriter.close() method to PGCopyWriter.finalize()
* Add PGCopyWriter.tell() method

## 0.1.2

* Add size parameter to PGCopy.read() method

## 0.1.1

* Fix read functions
* Add initialize PGCopyWriter from PGCopy object with method writer()

## 0.1.0

* Refactor over 60% code
* Remove self.columns
* Rename self.dtypes to self.pgtypes
* Change self.pgtypes object from PGDataType to PGOid
* Change self.__str__ & self.__repr__ output
* Add write functions
* Add class PGCopyWriter
* Add PGCopy.write method for initialize PGCopyWriter from PGCopy
* Add CHANGELOG.md

## 0.0.3

* Rename project to pgcopylib
* Refactor geometric types move from digits.py to geometrics.py
* Fix README.md
* Remove check -1 value in end of file for optimize PGCopy class initialization
* Publish library to Pip

## 0.0.2

* Add data type parsers
* Add geometric types
* Improve docs
* Rename Colums to Columns

## 0.0.1

First version of the library pgcopy_parser
