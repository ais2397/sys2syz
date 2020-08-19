import xml.etree.ElementTree as ET
import re
import os
import string
import logging

from core.Utils import *

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
    def __init__(self,target):
        self.target = target
        self.trees = []
        self.structs_and_unions = {}
        self.arguments = {}
        self.ptr_dir = None
        self.current_root = None
        for file in (os.listdir(self.target)):
            tree = ET.parse(self.target+file)
            self.trees.append(tree)

    def get_root(self, ident_name):
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

    def resolve_id(self, root, id):
        try:
            for element in root:
                if element.get("id") == id:
                    return element
                for child in element:
                    if child.get("id") == id:
                        return child
        except Exception as e:
            log.error(e)
            logging.debug("[*] Issue in resolving: %s", id)
        
    def get_id(self, root, ident_name):
        try:
            for element in root:
                if element.get("ident") == ident_name:
                    return self.get_type(element), element
                for child in element:
                    if child.get("ident") == ident_name:
                        return self.get_type(child), child
            logging.info("TO-DO: Find again")
            self.get_id(self.current_root, ident_name)
        except Exception as e:
            logging.error(e)
            logging.debug("[*] Issue in resolving: %s", ident_name)

    def get_type(self, child):
        try:
            if child.get("type") == "struct":
                logging.debug("TO-DO: struct")
                return self.build_struct(child)

            elif child.get("type") == "union":
                logging.debug("TO-DO: union")
                return self.build_union(child)

            elif child.get("type") == "function":
                logging.debug("TO-DO: function")
                return

            elif child.get("type") == "pointer":
                logging.debug("TO-DO: pointer")
                return self.build_ptr(child)

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

            elif child.get("type") == "enum":
                logging.debug("TO-DO: enum")
                desc_str = "flags["
                desc_str += child.get("ident")+"_flags]"
                return desc_str

            elif "base-type-builtin" in child.keys():
                logging.debug("TO-DO: builtin-type")
                return type_dict.get(child.get("base-type-builtin"))
            else:
                logging.debug("TO-DO: base-type")
                root = self.resolve_id(self.current_root, child.get("base-type"))
                return self.get_type(root)
        except Exception as (e):
            logging.error(e)
            logging.debug("Error occured while fetching the type")

    def build_ptr(self, child):
        try:
            logging.debug("[*] Building pointer")
            name = child.get("ident")
            if "base-type-builtin" in child.attrib.keys():
                base_type = child.get("base-type-builtin")
                if base_type =="void" or base_type == "char":
                    ptr_str = "buf[" + self.ptr_dir + "]"
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
        try:
            logging.debug("[*] Building struct")
            name = child.get("ident")
            if name not in self.structs_and_unions.keys():
                elements = []
                for element in child:
                    elem_type = self.get_type(element)
                    if elem_type == None:
                        elem_type = element.get("type") 
                    elements.append(element.get("ident") + "\t" + elem_type)
                    self.structs_and_unions[name] = "{\n" + "\n".join(elements) + "\n}\n"
            return str(name)
        except Exception as e:
            logging.error(e)
            logging.debug("Error occured while resolving the struct")

    def build_union(self, child):
        try:
            logging.debug("[*] Building union")
            name = child.get("ident")
            if name not in self.structs_and_unions:
                elements = []
                for element in child:
                    elem_type = self.get_type(element)
                    if elem_type == None:
                        elem_type = element.get("type") 
                    elements.append(element.get("ident") + "\t" + elem_type)
                    self.structs_and_unions[name] = "[\n" + "\n".join(elements) + "\n]\n"
            return str(name)
        except Exception as e:
            logging.error(e)
            logging.debug("Error occured while resolving the union")


    def pretty_structs(self):
        try:
            structs = ""
            for key in self.structs_and_unions:
                structs += (key + " " + self.structs_and_unions[key] +"\n")
            return structs
        except Exception as e:
            logging.error(e)
            logging.debug("[*] Error in parsing structs")


    def pretty_desc(self, fd):
        try:
            descriptions = ""
            if self.arguments is not None:
                for key in self.arguments:
                    desc_str = "ioctl$" + key + "("
                    fd_ = "fd " + fd
                    cmd = "cmd const[" + key + "]"
                    arg = "arg " + str(self.arguments[key])
                    desc_str += ", ".join([fd_, cmd, arg])
                    desc_str += ")\n"
                    descriptions += desc_str
            return descriptions
        except Exception as e:
            logging.error(e)
            logging.debug("[*] Error in parsing ioctl command descriptions")

    def make_file(self, struct_descriptions, header_files):
        try:
            includes = ""
            for file in header_files:
                includes += "include <" + file + ">\n"
            dev_name = self.target.split("/")[-3]
            fd_str = "fd_" + dev_name
            rsrc = "resource " + fd_str + "[fd]\n"
            open_desc = "syz_open_dev$" + dev_name.upper()
            open_desc += "(dev ptr[in, string[\"/dev/" + dev_name + "\"]], "
            open_desc += "id intptr, flags flags[open_flags]) fd_" + dev_name + "\n"
            func_descriptions = self.pretty_desc(fd_str)
            
            if func_descriptions is not None:
        
                desc_buf = "\n\n".join([includes, rsrc, open_desc, func_descriptions, struct_descriptions])
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
                                arg_type = raw_arg[1].get("type")
                                if arg_type in types:
                                    arg_str = "ptr[" + self.ptr_dir + ", "+ raw_arg[0]+ "]"
                                self.arguments[cmd] = arg_str
            return str(self.pretty_structs())
        except Exception as e:
            logging.error(e)
            logging.debug("Error while generating call descriptions")
