# Module : Description.py 
# Description : Contains functions which generate descriptions.
from core.Utils import *

import xml.etree.ElementTree as ET
import re
import os
import string
import logging
import collections

type_dict = {
    "unsigned char": "int8",
    "char": "int8",
    "unsigned short": "int16",
    "uint32_t": "int32",
    "unsigned int": "int32",
    "int": "int32",
    "unsigned long": "intptr",
    "long": "intptr",
    "void": "void"
}

types = ["struct", "union", "pointer"]

class Descriptions(object):
    def __init__(self,target, defined_flags):
        self.target = target
        self.defined_flags = defined_flags
        self.trees = []
        self.flags = []
        self.structs_and_unions = {}
        self.arguments = {}
        self.ptr_dir = None
        self.current_root = None
        MacroDetails = collections.namedtuple("MacroDetails", ["struct_name", "element_name", "macros"])
        for file in (os.listdir(self.target)):
            tree = ET.parse(self.target+file)
            self.trees.append(tree)

    def get_root(self, ident_name):
        """
        Find root for the tree storing element with its name as ident_name
        :return: root
        """

        try:
            for tree in self.trees:
                root = tree.getroot()
                for child in root:
                    if child.get("ident") == ident_name:
                        logging.debug("[*] Found Root ")
                        self.current_root = root
                        return root
        except Exception as e:
            logging.error(e)
            logging.debug('[*] Unable to find root')

    def resolve_id(self, root, find_id):
        """
        Find node having id value same as find_id
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
            logging.error(e)
            logging.debug("[*] Issue in resolving: %s", find_id)
        
    def get_id(self, root, find_ident):
        """
        Find node having ident value same as find_ident
        :return: 
        """

        try:
            for element in root:
                if element.get("ident") == find_ident:
                    return self.get_type(element), element
                for child in element:
                    if child.get("ident") == find_ident:
                        return self.get_type(child), child
            logging.info("TO-DO: Find again")
            self.get_id(self.current_root, find_ident)
        except Exception as e:
            logging.error(e)
            logging.debug("[*] Issue in resolving: %s", find_ident)

    def get_type(self, child):
        """
        Fetch type of an element
        :return:
        """

        try:
            #for structures
            if child.get("type") == "struct":
                logging.debug("TO-DO: struct")
                return self.build_struct(child)
            #for unions
            elif child.get("type") == "union":
                logging.debug("TO-DO: union")
                return self.build_union(child)
            #for functions
            elif child.get("type") == "function":
                logging.debug("TO-DO: function")
                return
            #for pointers
            elif child.get("type") == "pointer":
                logging.debug("TO-DO: pointer")
                return self.build_ptr(child)
            #for arrays
            elif child.get("type") == "array":
                logging.debug("TO-DO: array")
                desc_str = "array"
                if "base-type-builtin" in child.attrib.keys():
                    type_str = type_dict[child.get('base-type-builtin')]
                else:
                    root = self.resolve_id(self.current_root, child.get("base-type"))
                    type_str = self.get_type(root)
                size_str = child.get('array-size')
                desc_str += "[" + type_str + ", " + size_str + "]"
                return desc_str
            #for enums
            elif child.get("type") == "enum":
                logging.debug("TO-DO: enum")
                desc_str = "flags["
                desc_str += child.get("ident")+"_flags]"
                return self.build_enums
            #for nodes
            elif "base-type-builtin" in child.keys():
                logging.debug("TO-DO: builtin-type")
                return self.build_basetype(child)
            else:
                logging.debug("TO-DO: base-type")
                root = self.resolve_id(self.current_root, child.get("base-type"))
                return self.get_type(root)
        except Exception as e:
            logging.error(e)
            logging.debug("Error occured while fetching the type")

    def check_flag(self, name):
        print(self.defined_flags)
        return 1

    def build_basetype(self, child):
        child_type = type_dict.get(child.get("base-type-builtin"))
        if "int" in child_type:
            print(child_type + ": " + child.get("ident"))
            '''if check_flag(name):
                desc_str = "flags[" + name + "_flags]"'''
        return child_type

    def build_enums(self, child):
        try:
            name = child.get("ident")
            if check_flag(name):
                desc_str = "flags[" + name + "_flags]"
            else:
                desc_str = "flags[" + name + "_flags]"
                flags_undefined.append(desc_str)
            return desc_str
        except Exception as e:
            logging.error(e)
            print("Error occured while resolving enum")

    def build_ptr(self, child):
        """
        Build pointer
        :return: 
        """

        try:
            logging.debug("[*] Building pointer")
            name = child.get("ident")
            #get type of pointer
            if "base-type-builtin" in child.attrib.keys():
                base_type = child.get("base-type-builtin")
                #check if pointer stores char type value
                if base_type =="void" or base_type == "char":
                    ptr_str = "buffer[" + self.ptr_dir + "]"
                else:
                    ptr_str = "ptr[" + self.ptr_dir + ", " + str(type_dict[child.get("base-type-builtin")]) + "]"
            else:
                x = self.get_type(self.resolve_id(self.current_root,child.get("base-type")))
                ptr_str = "ptr[" + self.ptr_dir + ", " + x + "]"
            return ptr_str
        except Exception as e:
            logging.error(e)
            logging.debug("Error occured while resolving pointer")

    def build_struct(self, child):
        """
        Build struct
        :return: Struct identifier
        """

        try:
            len_regx = re.compile("(.+)len")
            logging.debug("[*] Building struct")
            name = child.get("ident")

            if name not in self.structs_and_unions.keys():
                elements = {}
                #get the type of each element in struct
                for element in child:
                    elem_type = self.get_type(element)
                    elem_ident = element.get("ident")
                    if elem_type == None:
                        elem_type = element.get("type") 
                    elements[element.get("ident")] = elem_type

                #check for the elements which store length of an array or buffer
                for element in elements:
                    len_grp = len_regx.match(element)
                    if len_grp is not None:
                        buf_name = len_grp.groups()[0]
                        matches = [search_str for search_str in elements if re.search(buf_name, search_str)] 
                        for i in matches:
                            if i is not element:
                                elem_type = "len[" + i + ", " + elements[element] + "]"
                                elements[element] = elem_type
                #format struct
                element_str = ""
                for element in elements: 
                    element_str += element + "\t" + elements[element] + "\n"
                self.structs_and_unions[name] = " {\n" + element_str + "}\n"
            return str(name)
        except Exception as e:
            logging.error(e)
            logging.debug("Error occured while resolving the struct")

    def build_union(self, child):
        """
        Build union
        :return: Union identifier
        """

        try:
            len_regx = re.compile("(.+)len")
            logging.debug("[*] Building union")
            name = child.get("ident")
            if name not in self.structs_and_unions:
                elements = {}
                #get the type of each element in union
                for element in child:
                    elem_type = self.get_type(element)
                    if elem_type == None:
                        elem_type = element.get("type") 
                    elements[element.get("ident")] = elem_type
                
                #check for the elements which store length of an array or buffer
                for element in elements:
                    len_grp = len_regx.match(element)
                    if len_grp is not None:
                        buf_name = len_grp.groups()[0]
                        matches = [search_str for search_str in elements if re.search(buf_name, search_str)] 
                        for i in matches:
                            if i is not element:
                                elem_type = "len[" + i + ", " + elements[element] + "]"
                                elements[element] = elem_type

                #format union
                element_str = ""
                for element in elements: 
                    element_str += element + "\t" + elements[element] + "\n"
                self.structs_and_unions[name] = " [\n" + element_str +"]\n"
            return str(name)
        except Exception as e:
            logging.error(e)
            logging.debug("Error occured while resolving the union")


    def pretty_structs(self):
        """
        Generates descriptions of structs and unions for syzkaller
        :return:
        """

        try:
            structs = ""
            for key in self.structs_and_unions:
                structs += (str(key) + str(self.structs_and_unions[key]) + "\n")
            return structs
        except Exception as e:
            logging.error(e)
            logging.debug("[*] Error in parsing structs")


    def pretty_ioctl(self, fd):
        """
        Generates descriptions for ioctl calls
        :return:
        """

        try:
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
            logging.error(e)
            logging.debug("[*] Error in parsing ioctl command descriptions")

    def make_file(self, header_files):
        """
        Generates a device specific file with descriptions of ioctl calls
        :return: Path of output file
        """

        try:
            print(self.defined_flags)
            print(self.defined_flags[0][2])
            includes = ""
            for file in header_files:
                includes += "include <" + file + ">\n"
            dev_name = self.target.split("/")[-3]
            fd_str = "fd_" + dev_name
            rsrc = "resource " + fd_str + "[fd]\n"
            open_desc = "syz_open_dev$" + dev_name.upper()
            open_desc += "(dev ptr[in, string[\"/dev/" + dev_name + "\"]], "
            open_desc += "id intptr, flags flags[open_flags]) fd_" + dev_name + "\n"
            func_descriptions = str(self.pretty_ioctl(fd_str))
            struct_descriptions = str(self.pretty_structs())
            
            if func_descriptions is not None:
                desc_buf = "#Autogenerated by sys2syz\n"
                desc_buf += "\n".join([includes, rsrc, open_desc, func_descriptions, struct_descriptions])
                output_file_path = os.getcwd() + "/out/" + "dev_" + dev_name + ".txt"
                output_file = open( output_file_path, "w")
                output_file.write(desc_buf)
                output_file.close()
                return output_file_path
            else:
                return None
        except Exception as e:
            logging.error(e)
            logging.debug("[*] Error in making device file")

    def run(self, extracted_file):
        """
        Parses arguments and structures for ioctl calls
        :return: True
        """

        try:
            with open(extracted_file) as ioctl_commands:
                commands = ioctl_commands.readlines()
                for command in commands:
                    parsed_command = list(command.split(", "))
                    self.ptr_dir, cmd, argument = parsed_command
                    if self.ptr_dir != "null":
                        argument_name = argument.split(" ")[-1].strip()
                        if argument_name in type_dict.keys():
                            self.arguments[cmd] = type_dict.get(argument_name)
                        else:
                            raw_arg = self.get_id(self.get_root(argument_name), argument_name)
                            if raw_arg is not None:
                                arg_str = raw_arg[0]
                                arg_str = "ptr[" + self.ptr_dir + ", "+ raw_arg[0]+ "]"
                                self.arguments[cmd] = arg_str
                    else:
                        self.arguments[cmd] = None
            return True
        except Exception as e:
            logging.error(e)
            logging.debug("Error while generating call descriptions")
