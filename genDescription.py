import xml.etree.ElementTree as ET
import sys
import re
import os
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
trees = []
structs_and_unions = {}
ptr_dir = None
current_root = None
for file in (os.listdir(sys.argv[1])):
    tree = ET.parse(sys.argv[1]+file)
    trees.append(tree)

class Generator(object):
    def __init__(self,target):
        comm_path = os.getcwd + "/preprocessed/" + target.split("/")[-1] + "ioctl_commands.txt"
        tree = ET.parse(sys.argv[1])
        root = tree.getroot()
        struct_nodes = []

def get_root(ident_name):
    global current_root
    try:
        for tree in trees:
            root = tree.getroot()
            for child in root:
                if child.get("ident") == ident_name:
                    logging.debug("[*] Found Root ")
                    current_root = root
                    return root
    except Exception as e:
        logging.error(e)
        logging.debug('[*] Unable to find root')

def resolve_id(root, id):
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
        
def get_id(root, ident_name):
    try:
        global current_root
        for element in root:
            if element.get("ident") == ident_name:
                return get_type(element)
            for child in element:
                if child.get("ident") == ident_name:
                    return get_type(child)
        logging.info("TO-DO: Find again")
        get_id(current_root, ident_name)
    except Exception as e:
        logging.error(e)
        logging.debug("[*] Issue in resolving: %s", ident_name)

def get_type(child):
    try:
        global current_root
        if child.get("type") == "struct":
            logging.debug("TO-DO: struct")
            return build_struct(child)
        elif child.get("type") == "union":
            logging.debug("TO-DO: union")
            return build_union(child)
        elif child.get("type") == "function":
            logging.debug("TO-DO: function")
            return
        elif child.get("type") == "pointer":
            logging.debug("TO-DO: pointer")
            return build_ptr(child)
        elif child.get("type") == "array":
            logging.debug("TO-DO: array")
            desc_str = "array"
            if "base-type-builtin" in child.attrib.keys():
                type_str = type_dict[child.get('base-type-builtin')]
            else:
                root = resolve_id(current_root, child.get("base-type"))
                type_str = get_type(root)
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
            #print("builtin type: " + child.get("base-type-builtin"))
            return type_dict.get(child.get("base-type-builtin"))
        else:
            logging.debug("TO-DO: base-type")
            root = resolve_id(current_root, child.get("base-type"))
            #print("Type: "+ str(child.get("type"))),
            #print("\tId:" + child.get("id")),
            #print("\tBase-Type: "+ str(child.get("base-type")))
            return get_type(root)
    except Exception as (e):
        logging.error(e)
        logging.debug("Error occured while fetching the type")

def build_ptr(child):
    try:
        global ptr_dir
        name = child.get("ident")
        if "base-type-builtin" in child.attrib.keys():
            base_type = child.get("base-type-builtin")
            if base_type =="void" or base_type == "char":
                ptr_str = "buf[" + ptr_dir + "]"
            else:
                ptr_str = "ptr[" + ptr_dir + ", " + str(child.get("base-type-builtin")) + "]"
        else:
            x = get_type(resolve_id(current_root,child.get("base-type")))
            ptr_str = "ptr[" + ptr_dir + ", " + x + "]"
        return ptr_str
    except Exception as e:
        logging.error(e)
        logging.debug("Error occured while resolving pointer")

def build_struct(child):
    try:
        logging.debug("[*] Building struct")
        global structs_and_unions
        name = child.get("ident")
        if name not in structs_and_unions.keys():
            elements = []
            for element in child:
                elem_type = get_type(element)
                if elem_type == None:
                    elem_type = element.get("type") 
                elements.append(element.get("ident") + "\t" + elem_type)
                structs_and_unions[name] = "{\n" + "\n".join(elements) + "\n}\n"
        return str(name)
    except Exception as e:
        logging.error(e)
        logging.debug("Error occured while resolving the struct")

def build_union(child):
    try:
        logging.debug("[*] Building union")
        name = child.get("ident")
        if name not in structs_and_unions:
            elements = []
            for element in child:
                elem_type = get_type(element)
                if elem_type == None:
                    elem_type = element.get("type") 
                elements.append(element.get("ident") + "\t" + elem_type)
                structs_and_unions[name] = "[\n" + "\n".join(elements) + "\n]\n"
        return str(name)
    except Exception as e:
        logging.error(e)
        logging.debug("Error occured while resolving the union")


def pretty_structs():
    global structs_and_unions
    for key in structs_and_unions:
        print(key + " " +structs_and_unions[key])

def pretty_desc(desc):
    fd = "fd"
    for key in desc:
        desc_str = "ioctl$" + key + "("
        desc_str += ", ".join([fd, key, str(desc[key])])
        desc_str += ")"
        print desc_str


def main():
    try:
        global ptr_dir, structs_and_unions, trees
        arguments = {}
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
        cwd = os.getcwd()
        extracted_file = cwd + "/preprocessed/" + sys.argv[1].split("/")[-3] + "/ioctl_commands.txt"
        with open(extracted_file) as ioctl_commands:
            commands = ioctl_commands.readlines()
            for command in commands:
                parsed_command = list(command.split(", "))
                ptr_dir, cmd, argument = parsed_command
                if ptr_dir != "null":
                    argument_name = argument.split(" ")[-1].strip()
                    if argument_name in type_dict.keys():
                        arguments[cmd] = type_dict.get(argument_name)
                    else:
                        arguments[cmd] = get_id(get_root(argument_name), argument_name)
                
        pretty_desc(arguments)
        pretty_structs()
    except Exception as e:
        logging.error(e)
        logging.debug("Error in main")

if __name__ == "__main__":
    main()