# Module : Description.py 
# Description : Contains functions which generate descriptions.
from core.utils import *
from core.logger import get_logger

from os.path import join
from fuzzywuzzy import fuzz, process
import xml.etree.ElementTree as ET
import re
import os
import string
 
type_dict = {
    "bool": "bool8",
    "unsigned char": "int8",
    "signed char": "int8",
    "char": "int8",
    "short": "int16",
    "unsigned short": "int16",
    "signed short": "int16",
    "uint32_t": "int32",
    "unsigned int": "int32",
    "int": "int32",
    "unsigned long": "intptr",
    "long": "intptr",
    "void": "void"
}

class Descriptions(object):
    def __init__(self, sysobj):
        self.sysobj = sysobj
        self.target = sysobj.target
        
        self.logger = get_logger("Descriptions", sysobj.log_level)

        self.gflags = {}
        self.structs_defs = {}
        self.union_defs = {}
        self.arguments = {}
        self.ptr_dir = None
        self.header_files = []
        self.current_root = None
        self.current_file = None
        self.functions = {}
        self.trees = {}
        if self.sysobj.input_type == "ioctl":
            self.ioctls = sysobj.ioctls
            self.flag_descriptions = sysobj.macro_details

    def get_root(self, ident_name):
        """
        Find root of the tree which stores an element whose ident value is <ident_name>
        :return: root
        """

        try:
            for tree in self.trees.keys():
                root = tree.getroot()
                for child in root:
                    if child.get("ident") == ident_name:
                        self.logger.debug("[*] Found Root ")
                        self.current_root = root
                        self.current_file = self.trees[tree].split(".")[0]
                        return root
        except Exception as e:
            self.logger.error(e)
            self.logger.warning('[*] Unable to find root')

    def resolve_id(self, root, find_id):
        """
        Find node having id value same as <find_id>, used for finding ident parameter for elements
        :return: node
        """

        try:
            for element in root:
                if element.get("id") == find_id:
                    return element
                for child in element:
                    if child.get("id") == find_id:
                        return child
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Issue in resolving: %s", find_id)
        
    def get_id(self, root, find_ident):
        """
        Find node having ident value same as find_ident
        :return: 
        """

        try:
            for element in root:
                #if element is found in the tree call get_type 
                #function, to find the type of argument for descriptions
                if element.get("ident") == find_ident:
                    self.logger.debug("- Generating desciption for "+ find_ident)
                    return self.get_type(element), element
                for child in element:
                    if child.get("ident") == find_ident:
                        self.logger.debug("- Generating desciption for "+ find_ident)
                        return self.get_type(child), child
            self.logger.debug("TO-DO: Find again")
            self.get_id(self.current_root, find_ident)
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Issue in resolving: %s", find_ident)

    def get_type(self, child, default_name=None):
        """
        Fetch type of an element
        :return:
        """

        try:
            #for structures: need to define each element present in struct (build_struct)
            if child.get("type") == "struct":
                self.logger.debug("TO-DO: struct")
                return self.build_struct(child, default_name)
            #for unions: need to define each element present in union (build_union)
            elif child.get("type") == "union":
                self.logger.debug("TO-DO: union")
                return self.build_union(child, default_name)
            #for functions
            elif child.get("type") == "function":
                self.logger.debug("TO-DO: function")
                return self.build_function(child, default_name)
            #for pointers: need to define the pointer type and its direction (build_ptr)
            elif child.get("type") == "pointer":
                self.logger.debug("TO-DO: pointer")
                return self.build_ptr(child, default_name)
            #for arrays, need to define type of elements in array and size of array (if defined)
            elif child.get("type") == "array":
                self.logger.debug("TO-DO: array")
                desc_str = "array"
                if "base-type-builtin" in child.attrib.keys():
                    type_str = type_dict[child.get('base-type-builtin')]
                else:
                    root = self.resolve_id(self.current_root, child.get("base-type"))
                    type_str = self.get_type(root)
                size_str = child.get('array-size')
                desc_str += "[" + type_str + ", " + size_str + "]"
                return desc_str
            #for enums: predict flag for enums (build_enums)
            elif child.get("type") == "enum":
                self.logger.debug("TO-DO: enum")
                desc_str = "flags["
                desc_str += child.get("ident")+"_flags]"
                return self.build_enums(child)
            #for nodes: 
            #builtin types 
            elif "base-type-builtin" in child.keys():
                return type_dict.get(child.get("base-type-builtin"))            
            #custom type
            else:
                self.logger.debug("TO-DO: base-type")
                root = self.resolve_id(self.current_root, child.get("base-type"))
                return self.get_type(root, default_name=default_name)
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Error occured while fetching the type")

    def instruct_flags(self, strct_name, name, strt_line, end_line, flg_type):
        try:
            self.logger.debug("[*] Checking for instruct flags.")
            flg_name = name + "_flag"
            file_name = self.current_file + ".i"
            if flg_name in self.gflags:
                flg_name = name + "_" + strct_name + "_flag" 
            flags = []
            if self.sysobj.input_type == "ioctl":
                for i in range(len(self.flag_descriptions[file_name])):
                    flag_tups = self.flag_descriptions[file_name][i]
                    if (int(flag_tups[1])>strt_line-1 and int(flag_tups[2])< end_line-1):
                        self.logger.debug("[*] Found instruct flags")
                        del self.flag_descriptions[file_name][i]
                        flags = flag_tups[0]
                        break
            else:
                cnt=0
                total = int(end_line) - strt_line -1
                for child in self.current_root:
                    if int(child.get("start-line")) in range(strt_line + 1 ,end_line):
                        cnt+=1
                        flags.append(child.get("ident"))
                    if cnt == total:
                        return
            if len(flags)>0 and None not in flags:
                self.gflags[flg_name] = ", ".join(flags)
                ret_str = "flags["+ str(flg_name) + ", " + str(flg_type) + "]"
            else:
                ret_str = None
            return ret_str
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Error in grabbing flags")
    
    def possible_flags(self, strct_name):
        """function to find possible categories of leftover flags
        """
        self.logger.debug("[*] Finding possible flags for " + strct_name)
        small_flag = []
        visited = [] 
        file = self.current_file + ".i"
        for i in range(len(self.flag_descriptions[file])):
            flags = self.flag_descriptions[file][i][0]
            small_flag.extend([i.lower() for i in flags])
        matches = [choice for (choice, score) in process.extract(strct_name, small_flag, scorer=fuzz.partial_ratio) if (score >= 50)]
        self.logger.info("[+] Possible flags groups for " + strct_name + ": ")
        for match in matches:
            find_str = match.upper()
            for i in range(len(self.flag_descriptions[file])):
                if (find_str in self.flag_descriptions[file][i][0]):
                    if (self.flag_descriptions[file][i][0] not in visited):
                        visited.append(self.flag_descriptions[file][i][0])
                        self.logger.info("[XX]" + str(self.flag_descriptions[file][i][0]))
                    break
        self.logger.info("-------------------------")

    def find_flags(self, name, elements, start, end):
        """Find flags present near a struct"""
        try:
            self.logger.debug("[*] Finding flags in vicinity of " + name )
            file_name = self.current_file + ".i"
            last_tup=len(self.flag_descriptions[file_name])
            #for flags after the struct
            max_line_no = self.flag_descriptions[file_name][0][2]
            min_line_no = self.flag_descriptions[file_name][last_tup-1][1]
            index = None
            for i in range(last_tup-1,0,-1):
                flags_tup = self.flag_descriptions[file_name][i]
                #find flags after the enf of struct, if start of flag tuple is < end of struct
                if flags_tup[1] < end:
                    if index == None:
                        break
                    min_tup = self.flag_descriptions[file_name][index]
                    print("\033[31;1m[ ** ] Found flags in vicinity\033[m of " + name + ": " + str(min_tup[0]))
                    if (self.append_flag()):
                        if (self.add_flag(min_tup[0], name)):
                            del self.flag_descriptions[file_name][index]
                    break
                elif (min_line_no > flags_tup[1]):
                    min_line_no = flags_tup[1]
                    index = i
            index = None
            for i in range(last_tup):
                flags_tup = self.flag_descriptions[file_name][i]
                #find flags present before start of struct, if end of flag tuple is > start of struct
                if flags_tup[2] > start:
                    if index == None:
                        break
                    max_tup = self.flag_descriptions[file_name][index]
                    print("\033[31;1m[ ** ] Found flags in vicinity\033[m of " + name + ": " + str(max_tup[0]))
                    if (self.append_flag()):
                        if (self.add_flag(max_tup[0], name)):
                            del self.flag_descriptions[file_name][index]
                    break
                elif (max_line_no < flags_tup[2]):
                    max_line_no = flags_tup[2]
                    index = i
            return
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Error in finding flags present near struct " + name)
    
    def append_flag(self):
        try:
            if (input("Add the predicted flags? (y/n): ") == "y"):
                return True
            return False
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Error in function: append_flag")

    def add_flag(self, flags, strct_name, element=None):
        try:
            if element is None:
                element = input("Enter the element name from " + strct_name + " to modify: ")
            flag_name = element + "_" + strct_name + "_flag"
            self.gflags[flag_name] = ", ".join(flags)
            if strct_name in self.structs_defs.keys():
                flag_type = self.structs_defs[strct_name][1][element]
                self.structs_defs[strct_name][1][element] = "flags["+flag_name + ", " + flag_type + "]"
                self.logger.debug("[*] New flag type added: " + self.structs_defs[strct_name][1][element])
                return True
            elif strct_name in self.union_defs.keys():
                flag_type = self.union_defs[strct_name][1][element]
                self.union_defs[strct_name][1][element] = "flags["+flag_name + ", " + flag_type + "]"
                self.logger.debug("[*] New flag type added: " + self.union_defs[strct_name][1][element])
                return True
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Error in function: add_flag")

    def break_enum(self, name, start, end):
        total = (end - start) -1
        cnt = 0
        for child in self.current_root:
            if int(child.get("start-line")) in range(start + 1 ,end):
                cnt+=1
                self.gflags[name].append(child.get("ident"))
            if cnt == total:
                return
            
    def build_enums(self, child):
        name = child.get("ident")
        self.logger.debug("[*] Building enum: " + name)
        if name:
            desc_str = "flags[" + name + "_flags, int8]"
            self.gflags[name + "_flags"]=[]
        self.break_enum(name + "_flags", int(child.get("start-line")), int(child.get("end-line")))
        return desc_str

    def build_ptr(self, child, default_name=None):
        """
        Build pointer
        :return: 
        """

        try:
            self.logger.debug("[*] Building pointer")
            if self.sysobj.input_type == "syscall":
                self.ptr_dir = input("Enter pointer direction: ")
            #pointer is a builtin type
            if "base-type-builtin" in child.attrib.keys():
                base_type = child.get("base-type-builtin")
                
                #check if pointer is buffer type i.e stores char type value
                if base_type =="void" or base_type == "char":
                    ptr_str = "buffer[" + self.ptr_dir + "]"

                else:
                    ptr_str = "ptr[" + self.ptr_dir + ", " + str(type_dict[child.get("base-type-builtin")]) + "]"
            #pointer is of custom type, call get_type function
            else:
                if default_name is not None and child.get('ident') is None:
                    self.logger.debug("- Generating desciption for "+ default_name)
                    x = self.get_type(self.resolve_id(self.current_root,child.get("base-type")), default_name)
                else:
                    x = self.get_type(self.resolve_id(self.current_root,child.get("base-type")))
                ptr_str = "ptr[" + self.ptr_dir + ", " + x + "]"
            return ptr_str
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Error occured while resolving pointer")

    def build_function(self, child, default_name=None):
        """
        Build function
        """
        func_name = child.get('ident')
        if func_name is None:
            func_name = default_name
        self.logger.debug("[*] Building function " + func_name)
        func_args={}
        func_ret = None
        for i, arg in enumerate(child):
            arg_name = arg.get('ident')
            if arg_name is None:
                arg_name='arg'+str(i)
            self.logger.debug("- Generating desciption for "+ arg_name)
            func_args[arg_name]=self.get_type(arg, arg_name)
        
        if child.get('base-type-builtin') == None:
            func_ret = self.get_type(self.resolve_id(child.get('base-type')))
            
        '''else:
            base_type = type_dict.get(child.get("base-type-builtin")))
            if "int" not in base_type or "void" not in base_type:
                func_str +=  base_type'''
        self.functions[func_name] = [func_args, func_ret]
        return func_name

    def build_struct(self, child, default_name="Deafult"):
        """
        Build struct
        :return: Struct identifier
        """

        try:
            #regex to check if name of element contains 'len' keyword
            len_regx = re.compile("(.+)len") 
            name = child.get("ident")
            if name is None:
                name = default_name
            if name not in self.structs_defs.keys():
                self.logger.debug("[*] Building struct: " + name)
                self.structs_defs[name] = []
                elements = {}
                prev_elem_name = "nill"
                strct_strt = int(child.get("start-line"))
                strct_end = int(child.get("end-line"))
                end_line = strct_strt
                prev_elem_type = "None"
                #get the type of each element in struct
                for element in child:
                    curr_name = element.get("ident")
                    self.logger.debug("- Generating desciption for "+ curr_name)
                    elem_type = self.get_type(element, curr_name)
                    start_line = int(element.get("start-line"))
                    #check for flags defined in struct's scope,
                    #possibility of flags only when prev_elem_type has 'int' keyword 
                    if ((start_line - end_line) > 1) and ("int" in prev_elem_type):
                        enum_name = self.instruct_flags(name, prev_elem_name, end_line, start_line, prev_elem_type)
                        if enum_name is None:
                            self.logger.debug("- Generating desciption for "+ curr_name)
                            elem_type = self.get_type(element, curr_name)                        
                        else:
                            elements[prev_elem_name]= enum_name
                    end_line = int(element.get("end-line"))
                    elements[curr_name] = str(elem_type)
                    prev_elem_name = curr_name
                    prev_elem_type = elem_type

                if (strct_end - start_line) > 1:
                    enum_name = self.instruct_flags(name, prev_elem_name, start_line, strct_end, elem_type)
                    if enum_name is None:
                        self.logger.debug("- Generating desciption for "+ curr_name)
                        elem_type = self.get_type(element, curr_name)                        
                    else:
                        elements[prev_elem_name]= enum_name
                #check for the elements which store length of an array or buffer
                for element in elements:
                    len_grp = len_regx.match(element)
                    if len_grp is not None:
                        buf_name = len_grp.groups()[0]
                        matches = [search_str for search_str in elements if re.search(buf_name, search_str)] 
                        for i in matches:
                            if i is not element:
                                if elements[element] in type_dict.values():
                                    elem_type = "len[" + i + ", " + elements[element] + "]"
                                elif "flags" in elements[element]:
                                    basic_type = elements[element].split(",")[-1][:-1].strip()
                                    elem_type = "len[" + i + ", " + basic_type + "]"
                                else:
                                    self.logger.warning("[*] Len type unhandled")
                                    elem_type = "None"
                                elements[element] = elem_type
                self.structs_defs[name] = [child, elements]
            return str(name)
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Error occured while resolving the struct: " + name)

    def build_union(self, child, default_name="Default"):
        """
        Build union
        :return: Union identifier
        """        
        #regex to check if name of element contains 'len' keyword
        
        len_regx = re.compile("(.+)len")
        name = child.get("ident")
        if name is None:
                name = default_name
        if name not in self.union_defs.keys():
            self.logger.debug("[*] Building union: " + name)
            elements = {}
            prev_elem_name = "nill"
            strct_strt = int(child.get("start-line"))
            strct_end = int(child.get("end-line"))
            end_line = strct_strt
            prev_elem_type = "None"
            #get the type of each element in union
            for element in child:
                curr_name = element.get("ident")
                self.logger.debug("- Generating desciption for "+ curr_name)
                elem_type = self.get_type(element, curr_name)
                start_line = int(element.get("start-line"))
                #check for flags defined in union's scope
                if ((start_line - end_line) > 1) and ("int" in prev_elem_type):                       
                    enum_name = self.instruct_flags(name, prev_elem_name, end_line, start_line, prev_elem_type)
                    if enum_name is None:
                        self.logger.debug("- Generating desciption for "+ curr_name)
                        elem_type = self.get_type(element, curr_name)                        
                    else:
                        elements[prev_elem_name]= enum_name
                end_line = int(element.get("end-line"))
                elements[curr_name] = str(elem_type)
                prev_elem_name = curr_name
                prev_elem_type = elem_type

            if (strct_end - start_line) > 1:
                enum_name = self.instruct_flags(name, prev_elem_name, start_line, strct_end, elem_type)
                if enum_name is None:
                    self.logger.debug("- Generating desciption for "+ curr_name)
                    elem_type = self.get_type(element, curr_name)                        
                else:
                    elements[prev_elem_name]= enum_name
            #check for the elements which store length of an array or buffer
            for element in elements:
                len_grp = len_regx.match(element)
                if len_grp is not None:
                    buf_name = len_grp.groups()[0]
                    matches = [search_str for search_str in elements if re.search(buf_name, search_str)] 
                    for i in matches:
                        if i is not element:
                            if elements[element] in type_dict.values():
                                elem_type = "len[" + i + ", " + elements[element] + "]"
                            elif "flags" in elements[element]:
                                basic_type = elements[element].split(",")[-1][:-1].strip()
                                elem_type = "len[" + i + ", " + basic_type + "]"
                            else:
                                self.logger.warning("[*] Len type unhandled")
                                elem_type = "None"
                            elements[element] = elem_type
            self.union_defs[name] = [child, elements]
        return str(name)

    def pretty_func(self):
        func_str = ""
        for func in self.functions.keys():
            func_str += func + "("
            func_str += ", ".join([name + " " + desc for name, desc in zip(self.functions[func][0].keys(), self.functions[func][0].values())]) + ") "
            if self.functions[func][1] is not None:
                func_str += self.functions[func][0]
            func_str+="\n"
        return func_str

    def pretty_structs_unions(self):
        """
        Generates descriptions of structs and unions for syzkaller
        :return:
        """

       
        self.logger.debug("[*] Pretty printing structs and unions ")
        pretty = ""
        for key in self.structs_defs:
            element_str = ""                
            node = self.structs_defs[key][0]
            element_names = self.structs_defs[key][1].keys()                
            strct_strt = int(node.get("start-line"))
            strct_end = int(node.get("end-line"))
            #get flags in vicinity of structs for ioctls
            if self.sysobj.input_type == "ioctl":
                self.find_flags(key, element_names, strct_strt, strct_end)
                #predictions fopossible_flagsr uncategorised flags
                self.possible_flags(key)
            for element in self.structs_defs[key][1]: 
                element_str += "\t" + element + "\t" + self.structs_defs[key][1][element] + "\n" 
            elements = " {\n" + element_str + "}\n"
            pretty += (str(key) + str(elements) + "\n")
        for key in self.union_defs:
            element_str = ""
            node = self.union_defs[key][0]
            element_names = self.union_defs[key][1].keys()                
            union_strt = int(node.get("start-line"))
            union_end = int(node.get("end-line"))
            #get flags in vicinity of unions for ioctls
            if self.sysobj.input_type == "ioctl":
                self.find_flags(key, element_names, union_strt, union_end)
                #predictions for uncategorised flags
                self.possible_flags(key)
            for element in self.union_defs[key][1]:
                element_str += "\t" + element + "\t" + self.union_defs[key][1][element] + "\n"
            elements = " [\n" + element_str + "]\n"
            pretty += (str(key) + str(elements) + "\n")
        return pretty
        


    def pretty_ioctl(self, fd):
        """
        Generates descriptions for ioctl calls
        :return:
        """

        try:
            self.logger.debug("[*] Pretty printing ioctl descriptions")
            descriptions = ""
            if self.arguments is not None:
                for key in self.arguments:
                    desc_str = "ioctl$" + key + "("
                    fd_ = "fd " + fd
                    cmd = "cmd const[" + key + "]"
                    arg = ""
                    if self.arguments[key] is not None:
                        arg = "arg " + str(self.arguments[key])
                        desc_str += ", ".join([fd_, cmd, arg])
                    else:
                        desc_str += ", ".join([fd_, cmd])
                    desc_str += ")\n"
                    descriptions += desc_str
            return descriptions
        except Exception as e:
            self.logger.error(e)
            self.logger.warning("[!] Error in parsing ioctl command descriptions")

    def make_file(self):
        """
        Generates a device specific file with descriptions of ioctl calls
        :return: Path of output file
        """

        self.logger.debug("[*] Generating description file")
        includes = ""
        include_path = "dev/" + os.path.basename(self.sysobj.target) + "/"
        flags_defn = ""
        for h_file in set(self.header_files):
            includes += "include <" + include_path + h_file + ">\n"
        dev_name = self.target.split("/")[-1]
        fd_str = "fd_" + dev_name
        rsrc = "resource " + fd_str + "[fd]\n"
        open_desc = "openat$" + dev_name.lower()
        open_desc += "(fd const[AT_FDCWD], file ptr[in, string[\"/dev/" + dev_name + "\"]], "
        open_desc += "flags flags[open_flags], mode const[0]) fd_" + dev_name + "\n"
        func_descriptions = str(self.pretty_ioctl(fd_str))
        struct_descriptions = str(self.pretty_structs_unions())
        for flg_name in self.gflags:
            flags_defn += flg_name + " = " + ", ".join(self.gflags[flg_name]) + "\n"           
        if func_descriptions is not None:
            desc_buf = "# Copyright 2018 syzkaller project authors. All rights reserved.\n# Use of this source code is governed by Apache 2 LICENSE that can be found in the LICENSE file.\n# Autogenerated by sys2syz\n\n"
            desc_buf += "\n".join([includes, rsrc, open_desc, func_descriptions, self.pretty_func() ,struct_descriptions, flags_defn])
            output_file_path = os.path.join(os.getcwd(),"out", self.sysobj.os, "dev_" + dev_name + ".txt")
            output_file = open( output_file_path, "w")
            output_file.write(desc_buf)
            output_file.close()
            return output_file_path
        else:
            return None

    def ioctl_run(self):
        """
        Parses arguments and structures for ioctl calls
        :return: True
        """
        self.xml_dir = self.sysobj.out_dir
        for xml_file in (os.listdir(self.xml_dir)):
            tree = ET.parse(join(self.xml_dir, xml_file))
            self.trees[tree] = xml_file
        self.flag_descriptions = self.sysobj.macro_details
        self.ioctls = self.sysobj.ioctls
        for command in self.ioctls:
            parsed_command = str(command).split(", ")
            self.ptr_dir, cmd, h_file, argument = parsed_command
            self.header_files.append(h_file)
            #for ioctl type is: IOR_, IOW_, IOWR_
            if self.ptr_dir != "null":
                
                #Get the type of argument                
                argument_def = argument.split(" ")[-1].strip()
                #when argument is of general type as defined in type_dict
                self.logger.debug("[*] Generating descriptions for " + cmd + ", args: " + argument_def)
                #if argument_name is an array
                if "[" in argument_def:
                    argument_def = argument_def.split("[")
                    argument_name = argument_def[0]
                elif "*" == argument_def:
                    if "void" in argument:
                        arg_str = "buf[" + self.ptr_dir + "]"
                        self.arguments[cmd] = arg_str
                        continue
                    else:
                        argument_name = argument.split(" ")[0]
                else:
                    argument_name = argument_def
                if argument_name in type_dict.keys():
                    self.arguments[cmd] = type_dict.get(argument_name)
                else:
                    raw_arg = self.get_id(self.get_root(argument_name), argument_name)
                    if raw_arg is not None:
                        ptr_def = raw_arg[0]
                        if type(argument_def) == list:
                            ptr_def = "array[" + raw_arg[0] + ", " + argument_def[1].split("]")[0] + "]"
                        
                        arg_str = "ptr[" + self.ptr_dir + ", "+ ptr_def+ "]"
                        self.arguments[cmd] = arg_str
            #for IO_ ioctls as they don't have any arguments
            else:
                self.arguments[cmd] = None
        return True

    def syscall_run(self):
        """
        Parses arguments and structures for ioctl calls
        :return: True
        """
        syscall_args = {}
        self.xml_dir = self.sysobj.out_dir
        for xml_file in (os.listdir(self.xml_dir)):
            tree = ET.parse(join(self.xml_dir, xml_file))
            self.trees[tree] = xml_file
        args_name = self.target + "_args"
        syscall_root = self.get_root(args_name)
        for element in syscall_root:
                #if element is found in the tree call get_type 
                #function, to find the type of argument for descriptions
            if element.get("ident") == args_name:
                for child in element:
                    self.logger.debug("- Function argument: " + child.get('ident'))
                    syscall_args[child.get('ident')]=self.get_syscall_arg(child.get('base-type'))
                break
        self.functions[self.target] = [syscall_args, None]
        flag_str = ""
        for flg_name in self.gflags:
                flag_str += flg_name + " = " + self.gflags[flg_name] + "\n"
        func_str = self.pretty_func()
        struct_union_str = self.pretty_structs_unions()
        print("--------------Description--------------\n")
        print("\n".join([func_str, struct_union_str, flag_str]))

    def get_syscall_arg(self, base_id):
        for element in self.resolve_id(self.current_root, base_id):
            if element.get('ident') == "le":
                element_base = self.resolve_id(self.current_root, element.get('base-type'))
                for child in element_base:
                    return self.get_type(child)

        
         
