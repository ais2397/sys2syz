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

trees = []
structs = []
ptr_dir = None
current_root = None
for file in (os.listdir(sys.argv[1])):
    tree = ET.parse(sys.argv[1]+file)
    trees.append(tree)

'''class Generator(object):
    def __init__(self,target):
        comm_path = os.getcwd + "/preprocessed/" + target.split("/")[-1] + "ioctl_commands.txt"
        tree = ET.parse(sys.argv[1])
        root = tree.getroot()
        struct_nodes = []'''

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
    except:
        logging.debug('[*] Unable to find root')
        return None

def resolve_type(root, id):
    try:
        re_id = re.compile("_[0-9]")
        for child in root:
            if child.get("id") == id:
                #print "Got element with id: " + id + "\nidentity: " + str(child.get("ident"))
                return child.get("ident"), child.get("id")
    except Exception as e:
        log.error(e)
        logging.debug("[*] Issue in resolving: %s", id)
        

def get_type(root, ident_name, id = None):
    try:
        global current_root
        logging.info("[+]Get type for %s", str(ident_name))
        i=0
        for child in root:
            #logging.debug("[+] Searching for " + ident_name + ": " + str(i) + " times.\n")
            i+=1
            #logging.debug(child.attrib)
            if child.get("ident") == ident_name:
                if id == None or child.get("id")==id:
                    if child.get("type") == "struct":
                        logging.info("TO-DO: struct")
                        return build_struct(child, root)
                    elif child.get("type") == "union":
                        logging.info("TO-DO: union")
                        return build_union(child)
                    elif child.get("type") == "function":
                        logging.info("TO-DO: function")
                        return
                    elif child.get("type") == "pointer":
                        #print (child.attrib)
                        logging.info("TO-DO: pointer")
                        return build_ptr(child)
                    elif child.get("type") == "array":
                        logging.info("TO-DO: array")
                        desc_str = "array"
                        type_str = type_dict[child.get('base-type-builtin')]
                        size_str = child.get('array-size')
                        desc_str += "[" + type_str + ", " + size_str + "]"
                        return desc_str
                    elif child.get("type") == "enum":
                        logging.info("TO-DO: enum")
                        desc_str = "flags["
                        desc_str += child.get("ident")+"_flags]"
                        return desc_str
                    elif "base-type-builtin" in child.keys():
                        logging.info("TO-DO: builtin-type")
                        return type_dict.get(child.get("base-type-builtin"))
                    else:
                        logging.info("TO-DO: base-type")
                        #print(child.get("base-type"))
                        #print ("[+] Base-type: attr" + str(child.attrib))
                        found_name, found_id = resolve_type(current_root, child.get("base-type"))
                        logging.debug("Find: %s", str(found_name))
                        logging.debug("Type: %s", str(child.get("type")))
                        logging.debug("Base-Type: %s", str(child.get("base-type")))
                        return get_type(current_root, found_name, found_id)
                    break
        logging.info("TO-DO: Find again")
        get_type(current_root, ident_name)
    except Exception as (e):
        logging.debug(e)

def build_ptr(child):
    try:
        global ptr_dir
        name = child.get("ident")
        if "base-type-builtin" in child.attrib.keys():
            base_type = child.get("base-type-builtin")
            if base_type =="void" or base_type == "char":
                ptr_str = "buf[" + ptr_dir + ", " + str(child.get("base-type-builtin")) + "]"
            else:
                ptr_str = "ptr[" + ptr_dir + ", " + str(child.get("base-type-builtin")) + "]"
        else:
            x = get_type(current_root, child.get("base-type"))
            ptr_str = "ptr[" + ptr_dir + ", " + child.get("base-type-builtin") + "]"
        return ptr_str
    except Exception as e:
        logging.error(e)

def build_struct(child, root):
    try:
        logging.debug("[*] Building struct")
        global structs
        name = child.get("ident")
        elements = []
        for element in child:
            #logging.debug("[*] Element: " +str(element.attrib.values()))
            elem_type = get_type(child , element.get("ident"))

            if elem_type == None:
                elem_type = element.get("type") 
            elements.append(element.get("ident") + "\t" + elem_type)
        #print(elements)
        desc_str = name + " {\n" + "\n".join(elements) + "\n}"
        if desc_str not in structs:
            structs.append(name + " {\n" + "\n".join(elements) + "\n}\n")
        return name
    except Exception as e:
        logging.error(e)

def build_union(name):
    try:
        logging.debug("[*] Building union")
        for struct in structs_and_unions:
            if name in struct.attrib.values():
                elements = []
                for element in struct:
                    elements.append(get_struct_element(element))
                return name + " [\n" + "\n".join(elements) + "\n]"
    except Exception as e:
        logging.error(e)

def main():
    try:
        global ptr_dir, structs, trees
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
        cwd = os.getcwd()
        extracted_file = cwd + "/preprocessed/" + sys.argv[1].split("/")[-3] + "/ioctl_commands.txt"
        with open(extracted_file) as ioctl_commands:
            commands = ioctl_commands.readlines()
            i=1
            for command in commands:
                #print("-"*24 + str(i) + "-"*24)
                parsed_command = command.split(", ")
                ptr_dir = parsed_command[0]
                if ptr_dir != "null":
                    print(parsed_command[1] + "\t-\t"),
                    argument = parsed_command[-1].split(" ")[-1].strip()
                    if argument in type_dict.keys():
                        print(type_dict.get(argument))
                    else:
                        print(get_type(get_root(argument), argument))
                i+=1
            print("-" * 24 + "Generated structs" + "-" * 24)
            print("\n".join(structs))
    except Exception as e:
        print("\n".join(structs))
        print(parsed_command)
        logging.error(e)

if __name__ == "__main__":
    main()