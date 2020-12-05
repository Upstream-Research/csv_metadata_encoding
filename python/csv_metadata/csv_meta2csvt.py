##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## This code is based on the csv-tools project source code, also by Upstream Research and available as open source.

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-META2CSVT tool version 20200406\n"
    "Creates a .csvt file from a CSV-Meta schema file.\n"
    "\n"
    "csv-meta2csvt [OPTIONS] InputFile\n"
    "\n"
    "OPTIONS\n"
    "    -c      Write .csvt file to stdout\n"
    "    -E {E}  Input file text encoding (e.g. 'utf-8', 'windows-1252')\n"
    "    --overwrite   Overwrite existing files\n"
    "\n"
)

import sys
import csv
import io
import os
import re

from ._csv_helpers import (
    decode_delimiter_name
    ,decode_charset_name
    ,decode_newline
    )

def main(arg_list, stdin, stdout, stderr):
    in_io = stdin
    out_io = stdout
    err_io = stderr
    show_help = False
    be_quiet = False
    should_overwrite = False
    should_write_stdout =False
    input_file_name = None
    output_file_name = None
    input_delimiter = ','
    input_quote_symbol = '"'
    output_delimiter = ','
    output_quote_symbol = '"'
    # 'std' will be translated to the standard line break decided by csv_helpers.decode_newline
    input_row_terminator = 'std'
    output_row_terminator = 'std'
    utf8_sig_charset_name = 'utf_8_sig'
    utf8_nosig_charset_name = 'utf_8'
    input_charset_name = utf8_sig_charset_name
    output_charset_name = None
    output_charset_error_mode = 'strict'
    input_charset_error_mode = 'strict'
    csv_cell_width_limit = 4*1024*1024  # python default is 131072 = 0x00020000
    in_row_count_max = None
    # [20160916 [db] I avoided using argparse in order to retain some flexibility for command syntax]
    arg_error = None
    arg_count = len(arg_list)
    arg_index = 1
    while (arg_index < arg_count):
        arg = arg_list[arg_index]
        if (arg == "--help" 
          or arg == "-?"
          ):
            show_help = True
        if (arg == "-q"
            or arg == "--quiet"
        ):
            be_quiet = True
        elif (arg == "-o"
          or arg == "--output"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_file_name = arg
        elif (arg == "-E"
          or arg == "--charset-in"
          or arg == "--encoding-in"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_charset_name = arg
        elif (arg == "-e"
          or arg == "--charset-out"
          or arg == "--encoding-out"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_charset_name = arg
        elif (arg == "--charset-in-error-mode"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_charset_error_mode = arg
        elif (arg == "--charset-out-error-mode"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_charset_error_mode = arg
        elif (arg == "--charset-error-mode"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_charset_error_mode = arg
                output_charset_error_mode = arg
        elif (arg == "-S"
          or arg == "--separator-in"
          or arg == "--delimiter-in"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_delimiter = arg
        elif (arg == "-s"
          or arg == "--separator-out"
          or arg == "--delimiter-out"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_delimiter = arg
        elif (arg == "-W"
          or arg == "--terminator-in"
          or arg == "--newline-in"
          or arg == "--endline-in"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                input_row_terminator = arg
        elif (arg == "-w"
          or arg == "--terminator-out"
          or arg == "--newline-out"
          or arg == "--endline-out"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                output_row_terminator = arg
        elif (arg == "--cell-width-limit"
          ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                csv_cell_width_limit = int(arg)
        elif (arg == "-N"
            or arg == "--max-rows-in"
        ):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                if ("all" == arg.lower()):
                    in_row_count_max = None
                else:
                    in_row_count_max = int(arg)
        elif (arg == "-c"
            or arg == "--stdout"
        ):
            should_write_stdout = True
        elif (arg == "-f"
            or arg == "--overwrite"
        ):
            should_overwrite = True
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == input_file_name):
                input_file_name = arg
        arg_index += 1
    
    if (None == input_file_name):
        show_help = True
        arg_error = "missing input file"
    else:
        column_meta_file_ext = ".schema"
        csvt_file_ext = ".csvt"
        (table_path, input_file_ext) = os.path.splitext(input_file_name)
        #maybe assert input_file_ext == ".csv"
        if (table_path.endswith(column_meta_file_ext)):
            table_path = table_path[:-len(column_meta_file_ext)]
        else:
            # The user gave us the main table file,
            #  but we want the .schema file:
            input_file_name = table_path + column_meta_file_ext + input_file_ext
        if (None == output_file_name and not should_write_stdout):
            output_file_name = table_path + csvt_file_ext
    if (None == arg_error
        and None != output_file_name
        and os.path.exists(output_file_name) 
        and not should_overwrite
        ):
        arg_error = "File exists '{0}', will not overwrite.".format(output_file_name)
    if (None != arg_error):
        if (show_help):
            err_io.write(help_text)
        err_io.write("Error: {}\n".format(arg_error))
    elif (show_help):
        out_io.write(help_text)
    else:
        if (None == output_charset_name):
            # special case to avoid BOM signatures in output files
            if (utf8_sig_charset_name == input_charset_name):
                output_charset_name = utf8_nosig_charset_name
            else:
                output_charset_name = input_charset_name
        input_charset_name = decode_charset_name(input_charset_name)
        output_charset_name = decode_charset_name(output_charset_name)
        input_row_terminator = decode_newline(input_row_terminator)
        output_row_terminator = decode_newline(output_row_terminator)
        input_delimiter = decode_delimiter_name(input_delimiter)
        output_delimiter = decode_delimiter_name(output_delimiter) 
        in_file = None
        out_file = None
        try:
            read_text_io_mode = 'rt'
            #in_newline_mode = ''  # don't translate newline chars
            in_newline_mode = input_row_terminator
            in_file_id = input_file_name
            in_close_file = True
            if (None == in_file_id):
                in_file_id = in_io.fileno()
                in_close_file = False
            in_io = io.open(
                 in_file_id
                ,mode=read_text_io_mode
                ,encoding=input_charset_name
                ,newline=in_newline_mode
                ,errors=input_charset_error_mode
                ,closefd=in_close_file
                )
            if (in_close_file):
                in_file = in_io
            write_text_io_mode = 'wt'
            out_newline_mode=''  # don't translate newline chars
            #out_newline_mode = output_row_terminator
            out_file_id = output_file_name
            should_close_out_file = True
            if (None == out_file_id):
                out_file_id = out_io.fileno()
                should_close_out_file = False
            out_io = io.open(
                 out_file_id
                ,mode=write_text_io_mode
                ,encoding=output_charset_name
                ,newline=out_newline_mode
                ,errors=output_charset_error_mode
                ,closefd=should_close_out_file
                )
            if (should_close_out_file):
                out_file = out_io

            in_csv = csv.reader(
                in_io
                ,delimiter=input_delimiter
                ,lineterminator=input_row_terminator
                ,quotechar=input_quote_symbol
                )
            out_csv = csv.writer(
                out_io
                ,delimiter=output_delimiter
                ,lineterminator=output_row_terminator
                ,quotechar=output_quote_symbol
                )
            execute(
                 in_csv
                ,out_csv
                ,err_io
                ,be_quiet
                )
        except BrokenPipeError:
            pass
        finally:
            if (None != in_file):
                in_file.close()
            if (None != out_file):
                out_file.close()

def execute(
     in_csv
    ,out_csv
    ,err_io
    ,be_quiet
    ):
    (column_name_list, schema_dict) = read_schema_dict(in_csv)
    if (None != column_name_list and None != schema_dict):
        out_row = list()
        for column_name in column_name_list:
            column_info = schema_dict[column_name]
            in_datatype_name = column_info.get("type", None)
            out_datatype_name = "String"
            if (None == in_datatype_name):
                out_datatype_name = "String"
            elif (in_datatype_name in ("int", "integer")):
                out_datatype_name = "Integer"
            elif (in_datatype_name in ("float", "numeric", "decimal")):
                out_datatype_name = "Real"
            out_row.append(out_datatype_name)
        out_csv.writerow(out_row)


def read_schema_dict(in_csv):
    """ Read table schema information into a dict of metafield dicts. 
    
        Returns an ordered list of table column names
        And a dictionary of column names to metafield dicts.
    """
    end_row = None
    in_header_row = next(in_csv, end_row)
    in_column_position = 0
    in_column_count = 0
    if (None != in_header_row):
        in_column_count = len(in_header_row)
    initial_cell_value = None
    if (in_column_count > in_column_position):
        initial_cell_value = in_header_row[in_column_position]
        in_column_position += 1
    schema_dict = None
    table_column_name_list = None
    if (None == in_header_row):
        pass
    elif (None == initial_cell_value or 0 == len(initial_cell_value)):
        # transposed format: table columns declared in subsequent columns of schema
        table_column_name_list = list()
        table_column_count = 0
        while (in_column_count > in_column_position):
            column_name = in_header_row[in_column_position]
            table_column_name_list.append(column_name)
            in_column_position += 1
            table_column_count += 1
        column_info_list = list()
        for column_name in table_column_name_list:
            column_info_list.append(dict())
        in_row = next(in_csv, end_row)
        while (end_row != in_row):
            in_column_position = 0
            in_column_count = len(in_row)
            metafield_name = None
            if (in_column_count > in_column_position):
                metafield_name = in_row[in_column_position]
            in_column_position += 1
            table_column_position = 0
            while (in_column_count > in_column_position
                    and table_column_count > table_column_position
                ):
                column_info = column_info_list[table_column_position]
                metafield_value = in_row[in_column_position]
                column_info[metafield_name] = metafield_value
                table_column_position += 1
                in_column_position += 1
            in_row = next(in_csv, end_row)
        schema_dict = dict()
        table_column_position = 0
        while (table_column_count > table_column_position):
            column_name = table_column_name_list[table_column_position]
            column_info = column_info_list[table_column_position]
            schema_dict[column_name] = column_info
            table_column_position += 1
    elif ("name" == initial_cell_value):
        # canonical format: table columns declared per row of schema
        metafield_name_list = list()
        metafield_column_count = 0
        while (in_column_count > in_column_position):
            metafield_name = in_header_row[in_column_position]
            metafield_column_count += 1
            in_column_position += 1
        schema_dict = dict()
        table_column_name_list = list()
        in_row = next(in_csv, end_row)
        while (end_row != in_row):
            in_column_count = len(in_row)
            in_column_position = 0
            column_name = None
            column_info = None
            if (in_column_count > in_column_position):
                column_name = in_row[in_column_position]
                column_info = dict()
            in_column_position += 1
            metafield_column_position = 0
            while (in_column_count > in_column_position
                    and metafield_column_count > metafield_column_position
                ):
                metafield_name = metafield_name_list[metafield_column_position]
                metafield_value = in_row[in_column_position]
                column_info[metafield_name] = metafield_value
                metafield_column_position += 1
                in_column_count += 1
            if (None != column_info):
                table_column_name_list.append(column_name)
                schema_dict[column_name] = column_info
            in_row = next(in_csv, end_row)
    else:
        # unknown format
        pass
    return (table_column_name_list, schema_dict)


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()


