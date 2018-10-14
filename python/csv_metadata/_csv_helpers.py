##  Copyright (c) 2016 Upstream Research, Inc.  All Rights Reserved.  ##

import os

## Maps a delimiter name (e.g. "tab") to a delimter value (e.g. "\t")
## This is mostly useful for tabs since Windows commandline makes it near impossible to specify without an alias name
def decode_delimiter_name(delimiter_name):
    delimiter = delimiter_name
    if (None == delimiter_name):
        pass
    elif ("tab" == delimiter_name.lower()
      or "\\t" == delimiter_name.lower()
      ):
        delimiter = "\t"
    elif ("space" == delimiter_name.lower()
      or "sp" == delimiter_name.lower()
      ):
        delimiter = " "
    elif ("comma" == delimiter_name.lower()):
        delimiter = ","
    elif ("pipe" == delimiter_name.lower()
      or "vbar" == delimiter_name.lower()
      or "verticalbar" == delimiter_name.lower()
      ):
        delimiter = "|"
    elif ("semicolon" == delimiter_name.lower()):
        delimiter = ";"
    return delimiter

def decode_charset_name(in_charset_name):
    out_charset_name = in_charset_name
    if (None != out_charset_name):
        out_charset_name = out_charset_name.lower()
        out_charset_name = out_charset_name.replace("-", "_")
        if ("windows-1252" == out_charset_name):
            out_charset_name = "cp1252"
    return out_charset_name

def decode_newline(in_newline_name):
    out_newline = in_newline_name
    if (None != out_newline):
        out_newline = out_newline.lower()
        out_newline = out_newline.replace("\\r", "\r")
        out_newline = out_newline.replace("\\n", "\n")
        out_newline = out_newline.replace("\\r\\n", "\r\n")
        if ("sys" == out_newline):
            out_newline = os.linesep
        elif ("std" == out_newline):
            out_newline = "\n"
            #out_newline = os.linesep
        elif ("cr" == out_newline
          or "macintosh" == out_newline
          or "mac" == out_newline
        ):
            out_newline = "\r"
        elif ("lf" == out_newline
          or "unix" == out_newline
        ):
            out_newline = "\n"
        elif ("crlf" == out_newline
          or "windows" == out_newline
          or "win" == out_newline
          or "dos" == out_newline
        ):
            out_newline = "\r\n"
    return out_newline
