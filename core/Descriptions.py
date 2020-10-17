# Module : Description.py 
# Description : Contains functions which generate descriptions.
from core.Utils import *

import xml.etree.ElementTree as ET
import re
import os
import string
import logging
import pylcs
import py_common_subseq as common_sub

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
    def __init__(self,target, flag_descriptions):
        self.target = target
        self.flag_descriptions = flag_descriptions
        self.trees = {}
        self.gflags = {}
        self.structs_and_unions = {}
        self.arguments = {}
        self.ptr_dir = None
        self.current_root = None
        self.current_file = None
        for file in (os.listdir(self.target)):
            tree = ET.parse(self.target+file)
            self.trees[tree] = file

    def get_root(self, ident_name):
        """
        Find root for the tree storing element with its name as ident_name
        :return: root
        """

        try:
            for tree in self.trees.keys():
                root = tree.getroot()
                for child in root:
                    if child.get("ident") == ident_name:
                        logging.debug("[*] Found Root ")
                        self.current_root = root
                        self.current_file = self.trees[tree].split(".")[0]
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
            #print("entered get_type for:" + str(child.attrib))
            #for structures
            if child.get("type") == "struct":
                #print("TO-DO: struct")
                logging.debug("TO-DO: struct")
                return self.build_struct(child)
            #for unions
            elif child.get("type") == "union":
                #print("TO-DO: union")
                logging.debug("TO-DO: union")
                return self.build_union(child)
            #for functions
            elif child.get("type") == "function":
                #print("TO-DO: function")
                logging.debug("TO-DO: function")
                return
            #for pointers
            elif child.get("type") == "pointer":
                #print("TO-DO: pointer")
                logging.debug("TO-DO: pointer")
                return self.build_ptr(child)
            #for arrays
            elif child.get("type") == "array":
                #print("TO-DO: array")
                logging.debug("TO-DO: array")
                desc_str = "array"
                if "base-type-builtin" in child.attrib.keys():
                    type_str = type_dict[child.get('base-type-builtin')]
                else:
                    root = self.resolve_id(self.current_root, child.get("base-type"))
                    type_str = self.get_type(root)
                #print("Tyoe str: " + type_str)
                size_str = child.get('array-size')
                #print("Size str: " + size_str)
                desc_str += "[" + type_str + ", " + size_str + "]"
                #print ("desc str: " + desc_str)
                return desc_str
            #for enums
            elif child.get("type") == "enum":
                #print("TO-DO: enum")
                logging.debug("TO-DO: enum")
                desc_str = "flags["
                desc_str += child.get("ident")+"_flags]"
                return self.build_enums(child)
            #for nodes
            elif "base-type-builtin" in child.keys():
                #print("TO-DO: builtin-type")
                return self.build_basetype(child)
            else:
                logging.debug("TO-DO: base-type")
                #print("TO-DO: base-type")
                root = self.resolve_id(self.current_root, child.get("base-type"))
                #print(child.get("base-type"))
                return self.get_type(root)
        except Exception as e:
            logging.error(e)
            logging.debug("Error occured while fetching the type")

    def check_flag(self, name):
        print(self.flag_descriptions)
        return 1

    def instruct_flags(self, strct_name, name, strt_line, end_line, flg_type):
        try:
            flg_name = name + "_flag"
            if flg_name in self.gflags:
                flg_name = name + "_" + strct_name + "_flag" 
            #print("For " + strct_name + " startline: " +str(strt_line) + ", endline: "+ str(end_line))
            flags = None
            #print(self.flag_descriptions)
            for flag_tups in self.flag_descriptions[self.current_file + ".i"]:
                #print(flag_tups)
                if (int(flag_tups[1])>strt_line-1 and int(flag_tups[2])< end_line-1):
                    logging.debug("[*] Found instruct flags")
                    self.flag_descriptions[self.current_file + ".i"] = self.flag_descriptions[self.current_file + ".i"]
                    flags = flag_tups[0]
                    break
            if flags is not None:
                self.gflags[flg_name] = ", ".join(flags)
                ret_str = "flags["+flg_name + ", " + flg_type + "]"
            else:
                ret_str = None               
            return ret_str
        except Exception as e:
            logging.error(e)
            logging.debug("Error in grabbing flags")
    
    def possible_flags(self, strct_name, elements=None):
        try:
            small_flg =[i.lower() for i in self.flag_descriptions]
            len_sub = pylcs.lcs_of_list(strct_name, small_flg)
            max_len = max(len_sub)
            print("[-] Predicted flags for: " + strct_name)
            for i in range(len(len_sub)):
                macro = self.flag_descriptions[i]
                if len_sub[i] == max_len:
                    if any(substring in small_flg[i] for substring in strct_name.split("_")):
                        print(self.flag_descriptions[i])
            print("-"*50)
        except Exception as e:
            logging.error(e)
            print("Error in searching for potential flags for" + strct_name)

    def find_flags(self, name, elements, start, end):
        try:
            end+=1
            flags=[]
            logging.debug("[+] Finding flags in vicinity for " + name )
            last_tup=len(self.flag_descriptions[self.current_file+ ".i"])
            '''max_start = 0
            min_end = 1000000000
            flags = []
            for child in self.current_root:
                #child_start = int(child.get("start-line"))
                child_end = int(child.get("start-line"))
                if (child_start < start) and (child_start > max_start):
                    max_start = child.get("start-line")
                if (child_end > end) and (child_end < min_end):
                    min_end = child.get("end-line")'''
            while(1):
                for flags_tup in self.flag_descriptions[self.current_file+ ".i"]:
                    if flags_tup[1]>end:
                        break
                    if flags_tup[1] == end:
                        if any(substring in flg.lower() for flg in flags_tup[0] for substring in name.split("_")[1:]):
                            print("[-] Found flags in vicinity of " + name + ": " + str(flags_tup[0]))
                            return
                        else:
                            for element in elements:
                                if any(element in flg.lower() for flg in flags_tup[0]):
                                    print("[-] Found flags in vicinity of " + name + " for " + element + ": " + str(flags_tup[0]))
                                    return
                if end>self.flag_descriptions[self.current_file+ ".i"][last_tup-1][1]:
                    logging.debug("No flag found")
                    return
                else:
                    end+=1
        except Exception as e:
            logging.error(e)
            print("Error in finding flags present near struct " + name)

    def build_basetype(self, child):
        child_type = type_dict.get(child.get("base-type-builtin"))
        '''if "int" in child_type:
            #print(child_type + ": " + child.get("ident"))
            if check_flag(name):
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
            name = child.get("ident")
            logging.debug("[*] Building struct " + name)
            #print("[*] Building struct " + name)
            if name not in self.structs_and_unions.keys():
                elements = {}
                prev_name = "nill"
                strct_strt = int(child.get("start-line"))
                strct_end = int(child.get("end-line"))
                end_line = strct_strt
                prev_elem_type = None
                #get the type of each element in struct
                for element in child:
                    #print("Building element " + str(element.get("ident")))
                    elem_type = self.get_type(element)
                    #print("elem_type: "+ str(elem_type))
                    start_line = int(element.get("start-line"))
                    #check for flags defined in struct's scope
                    if ((start_line - end_line) > 1) and ("int" in prev_elem_type):   
                        #print("Start line"+ str(start_line)+", End line: "+str(end_line))
                        elem_type_prev = self.instruct_flags(name, prev_name, end_line, start_line, prev_elem_type)
                        if elem_type_prev is not None:
                            elements[prev_name]= elem_type_prev
                    end_line = int(element.get("end-line"))
                    curr_name = element.get("ident")
                    '''if elem_type == None:
                        elem_type = element.get("type")'''
                        #print ("In struct " + name + ": " + element.get("ident") + ", " +elem_type)
                    elements[curr_name] = str(elem_type)
                    prev_name = curr_name
                    prev_elem_type = elem_type

                if (strct_end - start_line) > 1:
                    temp_type = self.instruct_flags(name, prev_name, start_line, strct_end, elem_type)
                    if temp_type is not None:
                        elements[prev_name] = temp_type
                #get flags in vicinity of struct
                self.find_flags(name, elements.keys(), strct_strt, strct_end)

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
                #print("returning: " + name)
            return str(name)
        except Exception as e:
            logging.error(e)
            logging.debug("Error occured while resolving the struct: " + name)

    def build_union(self, child):
        """
        Build union
        :return: Union identifier
        """

        try:
            len_regx = re.compile("(.+)len")
            name = child.get("ident")
            logging.debug("[*] Building union " + name)
            #print("[*] Building union " + name)
            if name not in self.structs_and_unions.keys():
                elements = {}
                prev_name = "nill"
                strct_strt = int(child.get("start-line"))
                strct_end = int(child.get("end-line"))
                end_line = strct_strt
                prev_elem_type = None
                #get the type of each element in union
                for element in child:
                    #print("Building element " + str(element.get("ident")))
                    elem_type = self.get_type(element)
                    #print("elem_type: "+ str(elem_type))
                    start_line = int(element.get("start-line"))
                    #check for flags defined in union's scope
                    if ((start_line - end_line) > 1) and ("int" in prev_elem_type):   
                        #print("Start line"+ str(start_line)+", End line: "+str(end_line))
                        elem_type_prev = self.instruct_flags(name, prev_name, end_line, start_line, prev_elem_type)
                        if elem_type_prev is not None:
                            elements[prev_name]= elem_type_prev
                    end_line = int(element.get("end-line"))
                    curr_name = element.get("ident")
                    '''if elem_type == None:
                        elem_type = element.get("type")'''
                        #print ("In union " + name + ": " + element.get("ident") + ", " +elem_type)
                    elements[curr_name] = str(elem_type)
                    prev_name = curr_name
                    prev_elem_type = elem_type

                if (strct_end - start_line) > 1:
                    temp_type = self.instruct_flags(name, prev_name, start_line, strct_end, elem_type)
                    if temp_type is not None:
                        elements[prev_name] = temp_type
                #get flags in vicinity of union
                self.find_flags(name, elements.keys(), strct_strt, strct_end)

                
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
                #self.possible_flags(key)
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
            includes = ""
            flags_defn = ""
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
            for flg_name in self.gflags:
                flags_defn += flg_name + " = " + self.gflags[flg_name] + "\n"

            if func_descriptions is not None:
                desc_buf = "#Autogenerated by sys2syz\n"
                desc_buf += "\n".join([includes, rsrc, open_desc, func_descriptions, struct_descriptions, flags_defn])
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
                print(self.flag_descriptions)
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
