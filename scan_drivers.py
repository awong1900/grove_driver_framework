#!/usr/bin/python

#   Copyright (C) 2015 by seeedstudio
#   Author: Jack Shao (jacky.shaoxg@gmail.com)
#
#   The MIT License (MIT)
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#   THE SOFTWARE.

import os
import sys
import re
import json


GROVE_DRIVERS_DIR = './grove_drivers'

def parse_one_driver_dir (driver_dir):
    files = []
    for f in os.listdir(driver_dir):
        full_path = os.path.join(driver_dir,f)
        if os.path.isfile(full_path) and (full_path.endswith(".h") or full_path.endswith(".cpp")):
            files.append(f)
    return files

def get_class_header_file (files):
    for f in files:
        if f.endswith(".h") and f.find("class") > -1:
            return f
    return ""

def parse_class_header_file (file):
    patterns = {}
    print file
    content = open(file, 'r').read()
    ##grove name
    grove_name = re.findall(r'^//GROVE_NAME\s+"(.+)"', content, re.M)
    print grove_name
    if grove_name:
        patterns["GroveName"] = grove_name[0]
    else:
        return ("can not find GROVE_NAME in %s"%file, {})
    ##interface type
    if_type = re.findall(r'^//IF_TYPE\s+([a-zA-z0-9]+)', content, re.M)
    print if_type
    if if_type:
        patterns["InterfaceType"] = if_type[0]
    else:
        return ("can not find IF_TYPE in %s"%file,{})
    ##class name
    class_name = re.findall(r'^class\s+([a-zA-z0-9_]+)', content, re.M)
    print class_name
    if class_name:
        patterns["ClassName"] = class_name[0]
    else:
        return ("can not find class name in %s"%file,{})
    ##construct function arg list
    arg_list = re.findall(r'%s\((.*)\);'%class_name[0], content, re.M)
    print arg_list
    if arg_list:
        patterns["ConstructArgList"] = arg_list[0].split(',')
    else:
        return ("can not find construct arg list in %s"%file,{})

    ## read functions
    read_functions = re.findall(r'bool\s+(read_[a-zA-z0-9_]+)\((.*)\);', content, re.M)
    print read_functions
    reads = {}
    for func in read_functions:
        args = func[1].split(',')
        args = [x.strip() for x in args]
        reads[func[0]] = args
    patterns["Outputs"] = reads

    ## write functions
    write_functions = re.findall(r'bool\s+(write_[a-zA-z0-9_]+)\((.*)\);', content, re.M)
    print write_functions
    writes = {}
    for func in write_functions:
        args = func[1].split(',')
        args = [x.strip() for x in args]
        writes[func[0]] = args
    patterns["Inputs"] = writes

    ## event
    # bool attach_event_handler(CALLBACK_T handler);
    event_attachments = re.findall(r'bool\s+(attach_event_handler)\((.*)\);', content, re.M)
    print event_attachments
    if len(event_attachments) > 0:
        patterns["HasEvent"] = True
    else:
        patterns["HasEvent"] = False

    return ("OK",patterns)



## main ##

if __name__ == '__main__':

    grove_drivers_abs_dir = os.path.abspath(GROVE_DRIVERS_DIR)
    grove_database = []
    failed = False
    failed_msg = ""
    for f in os.listdir(GROVE_DRIVERS_DIR):
        full_dir = os.path.join(GROVE_DRIVERS_DIR, f)
        grove_info = {}
        if os.path.isdir(full_dir):
            print full_dir
            files = parse_one_driver_dir(full_dir)
            class_file = get_class_header_file(files)
            if class_file:
                result, patterns = parse_class_header_file(os.path.join(full_dir,class_file))
                if patterns:
                    grove_info['IncludePath'] = full_dir
                    grove_info['Files'] = files
                    grove_info['ClassFile'] = class_file
                    grove_info = dict(grove_info, **patterns)
                    print grove_info
                    grove_database.append(grove_info)
                else:
                    failed_msg = "ERR: parse class file: %s"%result
                    failed = True
                    break
            else:
                failed_msg = "ERR: can not find class file of %s" % full_dir
                failed = True
                break
    if not failed:
        open("./database.json","w").write(json.dumps(grove_database))
        open("./scan_status.json","w").write("OK")
    else:
        open("./scan_status.json","w").write(failed_msg)

