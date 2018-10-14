##  Copyright (c) 2017-2018 Upstream Research, Inc.  All Rights Reserved.  ##
##  Subject to an 'MIT' License.  See LICENSE file in top-level directory  ##

## This code is based on the csv-tools project source code, also by Upstream Research and available as open source.

## #python-3.x
## python 2 does not work due mostly to issues with csv and io modules with unicode data

help_text = (
    "CSV-MKMETA tool version 20170302:20181014\n"
    "Creates CSV Metadata supplementary files by analyzing a CSV table file\n"
    "Copyright (c) 2017-2018 Upstream Research, Inc.\n"
    "\n"
    "csv-mkmeta [OPTIONS] InputFile\n"
    "\n"
    "OPTIONS\n"
    "    -E {E}  Input file text encoding (e.g. 'utf-8', 'windows-1252')\n"
    "    -N {N}  Analyze the first N rows of the input file (default='all')\n"
    "    -q      Quiet mode\n"
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
    input_file_name = None
    output_file_name = None
    input_delimiter = ','
    output_delimiter = ','
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
    file_format_name = None
    file_format_variant = 0
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
        elif (arg == "-f"
            or arg == "--overwrite"
        ):
            should_overwrite = True
        elif (arg == "--format"):
            if (arg_index < arg_count):
                arg_index += 1
                arg = arg_list[arg_index]
                file_format_name = arg
        elif (None != arg
          and 0 < len(arg)
          ):
            if (None == input_file_name):
                input_file_name = arg
        arg_index += 1
    
    if (None == input_file_name):
        show_help = True
        arg_error = "missing input file"
    if (None != file_format_name):
        if ("transposed" == file_format_name):
            file_format_variant = 1
        if ("archive" == file_format_name):
            file_format_variant = 2

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

            in_csv = csv.reader(
                 in_io
                ,delimiter=input_delimiter
                ,lineterminator=input_row_terminator
                )

            table_file_name = input_file_name
            if (None != output_file_name):
                table_file_name = output_file_name
            execute(
                 in_csv
                ,err_io
                ,be_quiet
                ,should_overwrite
                ,file_format_variant
                ,table_file_name
                ,output_charset_name
                ,output_delimiter
                ,output_row_terminator
                ,in_row_count_max
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
    ,err_io
    ,be_quiet
    ,should_overwrite
    ,file_format_variant
    ,table_file_name
    ,table_charset_name
    ,table_delimiter
    ,table_row_terminator
    ,in_row_count_max
    ):
    column_meta_file_ext = ".schema.csv"
    table_meta_file_ext = ".meta.csv"

    (table_base_name, table_file_ext) = os.path.splitext(table_file_name)

    column_meta_file_name = table_base_name + column_meta_file_ext
    table_meta_file_name = table_base_name + table_meta_file_ext
    table_name = os.path.basename(table_base_name)

    write_table_meta_file(
        in_csv
        ,err_io
        ,be_quiet
        ,should_overwrite
        ,file_format_variant
        ,table_meta_file_name
        ,table_name
        ,table_charset_name
        ,table_delimiter
        ,table_row_terminator
        ,in_row_count_max
    )
    write_column_meta_file(
        in_csv
        ,err_io
        ,be_quiet
        ,should_overwrite
        ,file_format_variant
        ,column_meta_file_name
        ,table_name
        ,table_charset_name
        ,table_delimiter
        ,table_row_terminator
        ,in_row_count_max
    )


def write_table_meta_file(
    in_csv
    ,err_io
    ,be_quiet
    ,should_overwrite
    ,file_format_variant
    ,table_meta_file_name
    ,table_name
    ,table_charset_name
    ,table_delimiter
    ,table_row_terminator
    ,in_row_count_max
    ):
    end_row = None

    table_meta_field_name_list = [
         "charset"
        ,"name"
        ,"title"
        ,"subject"
        ,"subject_title"
        ,"description"
        ,"revision"
        ,"release_time"
        ,"start_time"
        ,"end_time"
        ,"time"
        ,"source_name"
        ,"source_title"
        ,"source_url"
        ,"notes"
    ]
    table_meta_field_dict = {}

    table_meta_value_default = None

    # set defaults
    table_meta_charset_name = meta_charset_name_from_py_charset(table_charset_name)
    table_meta_field_dict["charset"] = table_meta_field_dict.get("charset", table_meta_charset_name)
    table_meta_field_dict["name"] = table_meta_field_dict.get("name", table_name)

    # Write .meta.csv file
    should_write_table_meta_file = False
    table_meta_file_exists = os.path.exists(table_meta_file_name)
    if (table_meta_file_exists):
        if (should_overwrite):
            should_write_table_meta_file = True
            if (not be_quiet):
                err_io.write("Overwriting existing file {}\n".format(table_meta_file_name))
        else:
            if (not be_quiet):
                err_io.write("File already exists {}, will not overwrite.\n".format(table_meta_file_name))
    else:
        should_write_table_meta_file = True
    if (should_write_table_meta_file):
        out_file_name = table_meta_file_name
        out_charset_name = table_charset_name
        write_text_io_mode = 'wt'
        out_newline_mode=''  # don't translate newline chars
        out_file = io.open(
            out_file_name
            ,mode=write_text_io_mode
            ,encoding=out_charset_name
            ,newline=out_newline_mode
            )
        try:
            out_csv = csv.writer(
                    out_file
                    ,delimiter=table_delimiter
                    ,lineterminator=table_row_terminator
                    )
            if (not be_quiet):
                err_io.write("Created file: {}\n".format(out_file_name))
            if (0 == file_format_variant
                or 1 == file_format_variant
                ):
                # write a header row
                header_row = [
                    "name"
                    ,"value"
                ]
                out_csv.writerow(header_row)
            for field_name in table_meta_field_name_list:
                field_value = table_meta_field_dict.get(field_name, table_meta_value_default)
                out_row = [
                    field_name
                    ,field_value
                ]
                out_csv.writerow(out_row)
        finally:
            out_file.close()
            out_file = None


def write_column_meta_file(
    in_csv
    ,err_io
    ,be_quiet
    ,should_overwrite
    ,file_format_variant
    ,column_meta_file_name
    ,table_name
    ,table_charset_name
    ,table_delimiter
    ,table_row_terminator
    ,in_row_count_max
    ):
    end_row = None

    # Write .schema.csv file
    should_write_column_meta_file = False
    column_meta_file_exists = os.path.exists(column_meta_file_name)
    if (column_meta_file_exists):
        if (should_overwrite):
            should_write_column_meta_file = True
            if (not be_quiet):
                err_io.write("Overwriting existing file {}\n".format(column_meta_file_name))
        else:
            if (not be_quiet):
                err_io.write("File already exists {}, will not overwrite.\n".format(column_meta_file_name))
    else:
        should_write_column_meta_file = True
    if (should_write_column_meta_file):
        decimal_separator = '.'
        decimal_regex = re.compile( r"\s*([-+])?(\d+)(\.\d+)?\s*")
        column_name_list = None
        column_meta_list = list()
        in_header_row = next(in_csv, end_row)
        if (end_row != in_header_row):
            column_name_list = list(in_header_row)
            column_position = 0
            while (column_position < len(column_name_list)):
                column_name = column_name_list[column_position]
                column_meta = dict()
                column_meta["column_name"] = column_name
                column_meta_list.append(column_meta)
                column_position += 1
            
            # analyze input table to try and infer column datatypes
            example_row = None
            in_row_count = 0
            in_row = next (in_csv, end_row)
            while (end_row != in_row
                and (None == in_row_count_max  or in_row_count < in_row_count_max)
            ):
                # remember an example row for later
                if (None == example_row):
                    example_row = list(in_row)
                column_position = 0
                while (column_position < len(column_meta_list)
                    and column_position < len(in_row)
                ):
                    column_meta = column_meta_list[column_position]
                    cell_value = in_row[column_position]

                    # treat empty strings as NULL since the CSV reader isn't smart about quoted cells
                    # maybe the csv dialect can be changed?
                    if (None != cell_value
                        and 0 == len(cell_value)
                    ):
                        cell_value = None

                    if (None == cell_value):
                        null_cell_value_count = column_meta.get("null_cell_value_count",0)
                        column_meta["null_cell_value_count"] = null_cell_value_count + 1
                    else:
                        not_null_cell_value_count = column_meta.get("not_null_cell_value_count",0)
                        column_meta["not_null_cell_value_count"] = not_null_cell_value_count + 1

                        cell_char_len = len(cell_value)
                        if (0 == cell_char_len):
                            empty_cell_count = column_meta.get("empty_cell_count",0)
                            column_meta["empty_cell_count"] = empty_cell_count + 1
                        else:
                            if (0 == len(cell_value.strip())):
                                blank_cell_count = column_meta.get("blank_cell_count",0)
                                column_meta["blank_cell_count"] = blank_cell_count + 1
                            cell_char_len_max = column_meta.get("char_count_max", cell_char_len)
                            if (cell_char_len_max < cell_char_len):
                                cell_char_len_max = cell_char_len
                            cell_char_len_min = column_meta.get("char_count_min", cell_char_len)
                            if (cell_char_len_min > cell_char_len):
                                cell_char_len_min = cell_char_len
                            column_meta["char_count_max"] = cell_char_len_max
                            column_meta["char_count_min"] = cell_char_len_min

                        cell_value_int = as_int(cell_value)
                        if (None == cell_value_int):
                            not_int_count = column_meta.get("not_int_count",0)
                            column_meta["not_int_count"] = not_int_count + 1
                        else:
                            cell_int_max = column_meta.get("int_max", cell_value_int)
                            if (cell_int_max < cell_value_int):
                                cell_int_max = cell_value_int
                            column_meta["int_max"] = cell_int_max

                        cell_value_float = as_float(cell_value)
                        if (None == cell_value_float):
                            not_float_count = column_meta.get("not_float_count",0)
                            column_meta["not_float_count"] = not_float_count + 1
                        else:
                            cell_float_max = column_meta.get("float_max", cell_value_float)
                            if (cell_float_max < cell_value_float):
                                cell_float_max = cell_value_float
                            column_meta["float_max"] = cell_float_max

                        # try to guess decimal precision
                        (sign_char,int_chars,frac_chars) = (None,None,None)
                        decimal_regex_match = decimal_regex.fullmatch(cell_value)
                        if (None != decimal_regex_match):
                            (sign_char,int_chars,frac_chars) = decimal_regex_match.group(1,2,3)
                        if (None != int_chars 
                            and 0 < len(int_chars)
                        ):
                            # 20170323 [db] TODO This block of code isn't working, need to figure out why
                            # TODO look for thousands separators
                            decimal_int_digit_count = len(int_chars)
                            decimal_frac_digit_count = 0
                            if (None != frac_chars
                                and len(frac_chars) > len(decimal_separator)
                            ):
                                decimal_frac_digit_count = len(frac_chars) - len(decimal_separator)
                            decimal_precision_digit_count = decimal_int_digit_count + decimal_frac_digit_count
                            decimal_scale_digit_count = decimal_frac_digit_count
                            decimal_precision_digit_count_max = column_meta.get("decimal_precision_digit_count_max",decimal_precision_digit_count)
                            decimal_precision_digit_count_min = column_meta.get("decimal_precision_digit_count_min",decimal_precision_digit_count)
                            decimal_scale_digit_count_max = column_meta.get("decimal_scale_digit_count_max",decimal_scale_digit_count)
                            decimal_scale_digit_count_min = column_meta.get("decimal_scale_digit_count_min",decimal_scale_digit_count)
                            if (decimal_precision_digit_count_max < decimal_precision_digit_count):
                                decimal_precision_digit_count_max = decimal_precision_digit_count
                            if (decimal_precision_digit_count_min > decimal_precision_digit_count):
                                decimal_precision_digit_count_min = decimal_precision_digit_count
                            if (decimal_scale_digit_count_max < decimal_scale_digit_count):
                                decimal_scale_digit_count_max = decimal_scale_digit_count
                            if (decimal_scale_digit_count_min > decimal_scale_digit_count):
                                decimal_scale_digit_count_min = decimal_scale_digit_count
                            column_meta["decimal_precision_digit_count_max"] = decimal_precision_digit_count_max
                            column_meta["decimal_precision_digit_count_min"] = decimal_precision_digit_count_min
                            column_meta["decimal_scale_digit_count_max"] = decimal_scale_digit_count_max
                            column_meta["decimal_scale_digit_count_min"] = decimal_scale_digit_count_min
                        
                        # check for a leading zero, this will help us distinguish code number strings from actual numbers
                        if (None == sign_char
                            and None != int_chars
                            and 1 < len(int_chars)
                            and int_chars[0] == '0'
                        ):
                            leading_zero_count = column_meta.get("leading_zero_count",0)
                            column_meta["leading_zero_count"] = leading_zero_count + 1

                        # end if (cell_value not None)
                    column_position += 1
                    # end while (column)
                in_row_count += 1
                in_row = next (in_csv, end_row)
                # end while (row)
            
            # Modify the column_meta_list with some datatype guesses

            column_type_name_str = "varchar"
            column_type_name_fixed_char = "char"
            column_type_name_int = "integer"
            column_type_name_float = "float"
            column_type_name_decimal = "decimal"
            column_type_name_default = column_type_name_str

            for column_meta in column_meta_list:
                column_type_name = None
                null_cell_value_count = column_meta.get("null_cell_value_count",0)
                not_null_cell_value_count = column_meta.get("not_null_cell_value_count",0)
                empty_cell_count = column_meta.get("empty_cell_count", None)
                cell_char_count_max = column_meta.get("char_count_max", None)
                cell_char_count_min = column_meta.get("char_count_min", None)
                not_int_count = column_meta.get("not_int_count",0)
                not_float_count = column_meta.get("not_float_count",0)
                leading_zero_count = column_meta.get("leading_zero_count",0)
                decimal_precision_digit_count_max = column_meta.get("decimal_precision_digit_count_max",None)
                decimal_precision_digit_count_min = column_meta.get("decimal_precision_digit_count_min",None)
                decimal_scale_digit_count_max = column_meta.get("decimal_scale_digit_count_max",None)
                decimal_scale_digit_count_min = column_meta.get("decimal_scale_digit_count_min",None)
                #not_null_count = column_meta.get("not_null_cell_value_count",0)
                if (0 == in_row_count
                    or 0 == not_null_cell_value_count
                ):
                    column_type_name = column_type_name_default
                elif (None != cell_char_count_max
                    and None != cell_char_count_min
                    and cell_char_count_max == cell_char_count_min
                    and (0 < not_float_count   # something is not a number, so it must be char type
                        or 0 < leading_zero_count  # something starts with a zero digit, so it looks like a digit code string
                    )
                ):
                    column_type_name = column_type_name_fixed_char
                elif (0 < leading_zero_count):
                    # assume anything that has a leading zero is a string
                    column_type_name = column_type_name_str
                elif (0 == not_int_count):
                    column_type_name = column_type_name_int
                elif (0 == not_float_count
                    and 0 < not_int_count
                    and None != cell_char_count_max
                    and 0 < cell_char_count_max
                ):
                    # it parses as a float, but mark its type as decimal
                    column_type_name = column_type_name_decimal
                else:
                    column_type_name = column_type_name_str

                column_size_str = None
                if (column_type_name_fixed_char == column_type_name):
                    column_size_str = str(cell_char_count_max)
                elif (column_type_name_str == column_type_name):
                    column_size_str = str(cell_char_count_max)
                elif (column_type_name_decimal == column_type_name):
                    if (None != decimal_precision_digit_count_max
                        and None != decimal_scale_digit_count_max
                    ):
                        column_size_str = "{},{}".format(
                            decimal_precision_digit_count_max
                            ,decimal_scale_digit_count_max
                        )

                # TODO finish adding int, float, decimal sizes
                
                # add new column_meta fields that computed above
                column_meta["data_type_name"] = column_type_name
                column_meta["data_type_size"] = column_size_str


            # Construct schema file contents
            out_row_list = list()

            if (0 == file_format_variant):
                # for variant 0, fields are rows in the schema file
                header_row = [
                    "name"
                    ,"type"
                    ,"size"
                    ,"pkey"
                    ,"unit"
                    ,"format"
                    ,"title"
                    ,"example"
                ]
                out_row_list.append(header_row)
                column_position = 0
                while (column_position < len(column_meta_list)):
                    column_meta = column_meta_list[column_position]
                    column_name = column_meta["column_name"]
                    column_type_name = column_meta["data_type_name"]
                    column_size_str = column_meta["data_type_size"]
                    column_key_state = None
                    column_unit_name = None
                    column_format_spec = None
                    column_title = None
                    example_value = example_row[column_position]
                    out_row = [
                        column_name
                        ,column_type_name
                        ,column_size_str
                        ,column_key_state
                        ,column_unit_name
                        ,column_format_spec
                        ,column_title
                        ,example_value
                    ]
                    out_row_list.append(out_row)
                    column_position += 1
            elif (1 == file_format_variant):
                # for variant 1, fields are columns in the schema file

                # header row, first cell is empty
                row_head_cell_value = None
                out_row = [row_head_cell_value]
                for column_meta in column_meta_list:
                    column_name = column_meta["column_name"]
                    out_row.append(column_name)
                out_row_list.append(out_row)

                row_head_cell_value = "type"
                out_row = [row_head_cell_value]
                for column_meta in column_meta_list:
                    column_type_name = column_meta["data_type_name"]
                    out_row.append(column_type_name)
                out_row_list.append(out_row)

                row_head_cell_value = "size"
                out_row = [row_head_cell_value]
                for column_meta in column_meta_list:
                    column_size_str = column_meta["data_type_size"]
                    out_row.append(column_size_str)
                out_row_list.append(out_row)

                row_head_cell_value = "pkey"
                out_row = [row_head_cell_value]
                for column_meta in column_meta_list:
                    column_key_state = None
                    out_row.append(column_key_state)
                out_row_list.append(out_row)

                row_head_cell_value = "unit"
                out_row = [row_head_cell_value]
                for column_meta in column_meta_list:
                    column_unit_name = None
                    out_row.append(column_unit_name)
                out_row_list.append(out_row)

                row_head_cell_value = "format"
                out_row = [row_head_cell_value]
                for column_meta in column_meta_list:
                    column_format_spec = None
                    out_row.append(column_format_spec)
                out_row_list.append(out_row)

                row_head_cell_value = "title"
                out_row = [row_head_cell_value]
                for column_meta in column_meta_list:
                    column_title = None
                    out_row.append(column_title)
                out_row_list.append(out_row)

                row_head_cell_value = "example"
                out_row = [row_head_cell_value]
                out_row += example_row
                out_row_list.append(out_row)

            out_file_name = column_meta_file_name
            out_charset_name = table_charset_name
            write_text_io_mode = 'wt'
            out_newline_mode=''  # don't translate newline chars
            out_file = io.open(
                 out_file_name
                ,mode=write_text_io_mode
                ,encoding=out_charset_name
                ,newline=out_newline_mode
            )
            if (not be_quiet):
                err_io.write("Created file: {}\n".format(out_file_name))
            try:
                out_csv = csv.writer(
                     out_file
                    ,delimiter=table_delimiter
                    ,lineterminator=table_row_terminator
                )
                for out_row in out_row_list:
                    out_csv.writerow(out_row)

            finally:
                out_file.close()
                out_file = None
            
            # end if (header row)
        # end if (schema file does not exist)

def meta_charset_name_from_py_charset(py_charset_name):
    '''
    Translate a python encoding name to a meta-csv charset name
    '''
    meta_charset_name = py_charset_name
    if (None != meta_charset_name):
        meta_charset_name = py_charset_name.lower()
        if ("utf_8_sig" == meta_charset_name):
            meta_charset_name = "UTF-8"
        elif ("utf_8" == meta_charset_name):
            meta_charset_name = "UTF-8"
        elif ("cp1252" == meta_charset_name):
            meta_charset_name = "WINDOWS-1252"
        elif ("iso-8859-1" == meta_charset_name):
            meta_charset_name = "LATIN1"
        elif ("latin_1" == meta_charset_name):
            meta_charset_name = "LATIN1"
        meta_charset_name = meta_charset_name.upper()
    return meta_charset_name

def as_int(s):
    n = None
    try:
        n = int(s)
    except ValueError:
        pass
    return n

def as_float(s):
    n = None
    try:
        n = float(s)
    except ValueError:
        pass
    return n


def console_main():
    main(sys.argv, sys.stdin, sys.stdout, sys.stderr)

        
if __name__ == "__main__":
    console_main()
