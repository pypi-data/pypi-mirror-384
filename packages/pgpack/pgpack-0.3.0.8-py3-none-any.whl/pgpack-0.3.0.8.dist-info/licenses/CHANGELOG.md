# Version History

## 0.3.0.8

* Update depends pgcopylib==0.2.1.8
* Add automake universal wheel

## 0.3.0.7

* Update depends pgcopylib==0.2.1.7
* Update depends light_compressor==0.0.1.7
* Update depends setuptools==80.9.0

## 0.3.0.6

* Delete polars_schema its interferes with correct operation to_polars() method
* Fix pandas_astype

## 0.3.0.5

* Change PGPackReader & PGPackWriter tell() method
* Add numpy data types to AssociatePyType dictionary

## 0.3.0.4

* Update requirements.txt depends pgcopylib==0.2.1.6
* Update requirements.txt depends light_compressor==0.0.1.6
* Fix PGPackWriter from_rows() function
* Add PGPackWriter.__init_copy() function

## 0.3.0.3

* Add MANIFEST.in
* Add tell() & close() methods to PGPackReader & PGPackWriter
* Update requirements.txt depends pgcopylib==0.2.1.5
* Update requirements.txt depends light_compressor==0.0.1.5

## 0.3.0.2

* Add metadata_reader import

## 0.3.0.1

* Small refactor PGPackWriter 
* Update requirements.txt depends pgcopylib==0.2.1.4
* Add MIT License

## 0.3.0.0

* Delete python internal compressed libraryes
* Change requirements.txt
* Change methods & class attributes
* Change write strategy
* Change default write compression to ZSTD
* Update README.md
* Redistribute project directories
* Refactor PGPackReader & PGPackWriter classes
* Compressed core change to light-compressor
* Fix detect_oid function for pandas.Timestamp type
* Fix pandas.DataFrame string dtype from object to string[python]

## 0.2.0.1

* Update requirements.txt depends pgcopylib==0.2.1.2
* Add pandas.DataFrame & polars.DataFrame cast dtypes for PGPackReader

## 0.2.0.0

* Update requirements.txt depends pgcopylib==0.2.0.1
* Change methods to new pgcopylib library
* Add attribute metadata with uncompress metadata bytes

## 0.1.3.1

* Add array nested into metadata
* Add property method to CompressionMethod
* Update README.md

## 0.1.3

* Add PGParam class
* Add values length and numeric precision/scale
* Add pgparam attibute into PGPackReader and PGPackWriter
* Fix ZSTD unpacked length where write with to_python() method
* Update requeriments.txt

## 0.1.2

* Rename project to pgpack
* Rename classes from PGCrypt* to PGPack*
* Change header to b"PGPACK\n\x00"
* Add size parameter into to_python, to_pandas, to_polars and to_bytes methods
* Update requirements.txt
* Fix nan values from pandas.DataFrame

## 0.1.1

* Add CHANGELOG.md
* Update README.md
* Improve ZstdDecompressionReader.seek() method

## 0.1.0

* Add methods from_python(),  from_pandas(),  from_polars() to PGPackWriter
* Add detect_oid function for generate oids from python types
* Add metadata_from_frame function
* Rename dtypes to pgtypes
* Change PGDataType to PGOid in pgtypes
* New __str__ and __repr__ output in PGPackReader and PGPackWriter

## 0.0.4

* Add support CopyByffer object as buffer

## 0.0.3

* Remove columns count from __str__ method

## 0.0.2

* Fix ZstdDecompressionReader.readall()
* Add docstring into __init__.py
* Improve docs
* Publish library to Pip

## 0.0.1

First version of the library pgcrypt
