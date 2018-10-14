CSV-MDE - CSV Metadata Encoding
===============================

Copyright (c) 2016-2018 Upstream Research Inc.

2016-07-27 (db) Created
2018-10-14 (db) Revised


Introduction
------------

This document specifies a format for encoding metadata for tabular data.
Such metadata includes descriptive information about the data table itself
as well as data type information associated with table columns.

The Comma Separated Value (CSV) format (RFC 4180) 
is a loosly defined format which is convenient for storing tabular datasets.
Historically there has not been any widely adopted convention 
for encoding metadata attributes and columnar "schema" attributes 
associated with the table encoded in a CSV document.
This specification attempts to provide a relatively simple means 
for encoding such attributes using the CSV format itself.

The format proposed herein differs from most other CSV metadata formats
since it encodes the metadata as CSV too.
Thus, there is no requirement to support additional data formats such as JSON, XML, or YAML.

The basic mechanism for storing the metadata defined here
encodes the metadata in a set of files
that will be stored along-side the primary table file 
using the same base file name, but suffixed with different file "extensions".

Since HTTP does not make it convenient to transmit extra files such as those proposed here,
we also propose an "archive" format,
which allows all of the metadata to be serialized into a single file.

This format is intended to be relatively simple to use by technicians accustomed
to using spreadsheet programs (such as Microsoft Excel) to edit and prepare CSV data
as well as to allow machine-processing of metadata.
It does not attempt to supercede the other CSV metadata formats already available.
The point is to make it relatively convenient to add some sort of metadata to existing datasets
even if that metadata is not as conformant, conventional, complex, or comprehensive as might be desired.


CSV Metadata Encoding: Multi-file Canonical Format
--------------------------------------------------

The basic metadata encoding format propsed here assumes that one already has a file of 
CSV formatted tabular data, the first row of which (i.e. the "header" row)
contains names for the columns in the table.
We shall call this original file the *Primary Table* file.

Example Primary Table contents:

    state_code,state_name,area_sq_km
    AL,Alabama,135767
    AK,Alaska,1723337
    AZ,Arizona,295234
    AK,Arkansas,137732
    CA,California,423967
    CO,Colorado,269601

Suppose the primary table file is named `<basename>.csv`.
We now supplement the primary table file with additional files
which are described in the sections which follow:

  * `<basename>.meta.csv` : *Table Metadata* file
  * `<basename>.schema.csv` : *Column Metadata* file

    
### Table Metadata File Format ###

The Table Metadata file is a CSV table with at least two columns.
The first column stores "meta-field" names and the second column stores the associated values.

The Table Metadata file should have a header row with the following names:

  1. `name`
  2. `value`

Additional columns may be added in the future, and client programs that do not recognize them should ignore them. 
All Metafield names are optional and are flexible in their definition.  
The specific names used in a metadata file will have to evolve by convention.  
It is recommended that metafield names be written in lower case with underscores.  
Metafield values should be simple (single-valued) when possible.

Although all metafields are optional, the following structure should be observed:
  
  * The first metafield (row) should be for the `charset` metafield
  * The second metafield (row) should be for the `name` metafield

Recommended metafield names are:

  * `charset` - to describe the character encoding of the primary CSV table file (more details below)
  * `name` - preferred name for identifying the dataset (dataset name should be all lower-case)
  * `title` - preferred title for displaying the dataset (title should be written in title-case)
  * `subject` - name to identify the subject of the dataset (lower-case identifier) (e.g. "population")
  * `subject_title` - title for displaying the dataset subject (e.g. "Adult Population")
  * `release_time` - year or YYYY-MM-DD when the dataset was first made available
  * `start_time` - year, date, or date-time when data collection began
  * `end_time` - year, date, or date-time when data collection was finished
  * `time` - year, date, or date-time to associate with the data collection (usually the end_date)
  * `time_precision` - the resolution for time values, should be `year`, `month`, `day`, `hour`, etc.
  * `source_name` - preferred name to identify the source of the data (all lower-case) (e.g. "us-cdc")
  * `source_title` - preferred title for displaying the dataset source (e.g. "US Center for Disease Control")
  * `source_url` - website where dataset was found
  * `description` - a human readable description of the data in the dataset
  * `revision` - a code that indicates when the data was last modified (e.g. "20161109")
  * `notes` - additional information helpful for understanding how to interpret the data

Example Table Metadata file contents:

    name,value
    charset,utf-8
    name,state_area_measurements
    title,State Area Measurements
    subject,geographic_area
    subject_title,Geographic Area
    time,2010-08-01
    time_precision,month
    source_name,us_census_state_area
    source_title,US Census
    source_url,https://www.census.gov/geo/reference/state-area.html
    description,US States and their area sizes


### Column Metadata File Format ###

The Column Metadata (schema) file contains a table of metadata for the columns (aka. fields) of the Primary Table.
The Field Metadata file stores a "matrix" of field metadata values using both a "header row" and a "header column".
The first row (i.e. the header row) contains metafield names such as "type", "size", etc. as described below.
The first column (i.e. the header column) contains the column names from the primary table in the order in which they appear in the primary table.

The first cell in the first column and first row is called the *initial cell* in the table.
The initial cell should be set to the character string `name`,
which expresses that the cells in the first column 
will contain the names of columns from the primary table.

As stated, the rest of the cells in the header row are metafield names.
By convention, the subsequent metafield columns should be `type` and `size`.

Most metafields in the schema file are optional.  Metafields are meant to be flexible, and will evolve by convention.

Metafield names are _not_ unique.  
This means that programs that read the column metadata CSV file should be prepared for duplicate names in the header row.
In practice, it is not necessary to duplicate column names, so this feature need not be used.

Recommended metafields are:

  * `type` - basic data-type name of the primary CSV table columns.  Data-type names should be one of:

    * `text` or `varchar`  - variable length character data
    * `char` - fixed-length character data
    * `byte` - fixed-length binary data (encoded as characters)
    * `varbinary` - variable length binary data (encoded as characters)
    * `numeric`  - generic numeric values
    * `integer`  - integral values (no decimal point)
    * `float` - floating-point, base-2 real number values
    * `decimal`  - base-10 real number values (like monetary values)
    * `boolean` - true/false (bit) value
    * `time` - a point in time - may include date (e.g. 2016-09-04 18:00:00)
    * `geometry` - geospatial complex point/line/polygon data
    
  * `size` - describes the size of data in the column.
  
    * For `text`/`varchar` data types, the size is the maximum number of characters permitted.
    * For `char` data type, the size is the maximum and the minimum number of characters permitted.
    * For `numeric` and `decimal` data types, this can be the significant figures (precision) and the number of fractional digits (scale) separated by either a decimal point or by a comma.
    * For `float` data types, this can be the number of bytes (4 for single precision, 8 for double precision)
    * For `integer` data types, this can be the number of bytes (4 for 32-bit, 8 for 64-bit)
    * For geospatial data types, this should be `point`, `linestring`, `polygon`, `multipoint`, `multilinestring`, `multipolygon`
      
  * `unit` - describes the interpretation of data in the column.  
    
    * For columns that describe physical measurements, this is a "unit of measurement" (e.g. "meter", "lbs")
    * For "id code" fields, this describes the type of code (e.g. "Us_state_county_fips").
    * For `time`, the `unit` should be left unspecified
    * For geospatial data, this should be a spatial reference identifier (e.g. "EPSG:4326", "WGS84")
      
  * `format` - describes the format of the field values in the data

    * for `byte` and `varbinary` this should be the encoding method, e.g. "hexadecimal", "base-64".
    * for `boolean` this should be in a form like "true/false", "1/0", "Y/N", "YES/NO" ("1/0" is recommended)
    * for `time`, this can be a time format string (e.g. YYYY-MM-DD)
    * for `geometry`, this might be "WKT", "geoJSON"
      
  * `key` - indicates a unique key metafield.  
    There may be more than one `key` metafield.  The first is considered the primary key.
    All columns that are part of the key should be marked with a `1` (number one), and all other columns should be left empty (NULL).

  * `example` - an example of a datum value for the corresponding field.
     There may be multiple `example` metafields.

Example Field Metadata File Contents:

    name,type,size,unit,key
    state_code,char,2,2-letter abbreviation,1
    state_name,varchar,64,display name,
    area_sq_km,integer,4,sq_km,


CSV Metadata Encoding: Variant Multi-file Transposed Format
-----------------------------------------------------------

The Multi-file Transposed format is a variant of the canonical format
where the rows and columns in the Column Metadata file are swapped ("transposed").
The advantage of this format is that the columns of the column metadata file
correspond to the columns of the primary table file.

In this format, the initial cell should be left empty;
that is, it should not be set to `name` as in the canonical format.

Example of Transposed Format file contents:

    ,state_code,state_name,area_sq_km
    type,char,varchar,integer
    size,2,64,4
    unit,2-letter abbreviation,name,sq_km
    key,1,,


CSV Metadata Encoding: Single-file Archive Format
-------------------------------------------------

It may be useful to encode the metadata into the same file as the data itself.
In this "archive" format, the file contents consist of the concatenation of the data in the following order:

  # The Table Metadata file
  # Optional blank lines
  # The Transposed Column Metadata file
  # The Primary table without the header row and with an empty column prepended

It is recommended that the data be saved with the following name format:

    <basename>.archive.csv

This format may be extended in the future.  
It is possible to store multiple tables of data in one file using this method of encoding,
and this feature may eventually be added to the specification.

Example of Archive Format contents:

    name,value
    charset,utf-8
    name,state_area_measurements
    title,State Area Measurements
    subject,geographic_area
    subject_title,Geographic Area
    time,2010-08-01
    time_precision,month
    source_name,us_census_state_area
    source_title,US Census
    source_url,https://www.census.gov/geo/reference/state-area.html
    description,US States and their area sizes

    ,state_code,state_name,area_sq_km
    type,char,varchar,integer
    size,2,64,4
    unit,2-letter abbreviation,name,sq_km
    key,1,,
    ,AL,Alabama,135767
    ,AK,Alaska,1723337
    ,AZ,Arizona,295234
    ,AK,Arkansas,137732
    ,CA,California,423967
    ,CO,Colorado,269601



CHARACTER ENCODING
------------------

The preferred character encoding is UTF-8 (with no "BOM" signature).  
UTF-16 (Windows "Unicode") is not recommended.  
To indicate a specific character encoding, the first non-header row of the table metadata file 
should specify the encoding name in a well-known form with the table metafield name `charset`.
It will be difficult to ensure that this metafield is accurate.
Software that reads these files should be prepared for mismatches.  
If a mismatch is detected, the dataset should be rejected (gracefully of course).  
There is no practical standard for character encoding names, so the character encoding name should be as conventional as possible (e.g. "Latin1", "Windows-1252", etc.).


HISTORY
-------

    2016-07-27 (db) Created
    2018-10-14 (db) Published with major revisions as "CSV Metadata Encoding"

