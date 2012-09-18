"""This module generate Python code for C structs.

Date April 2010
Created by ykk
"""
import datetime
import pylibopenflow.cheader as cheader
import os.path

class cppizer:
    """Class that put C++ wrapper around C structures
    
    Date April 2010
    Created by ykk
    """ 
    def __init__(self, cheaderfile, pyrules = None, tab="    "):
        """Initialize
        """
        ##Rules
        if (pyrules == None):
            self.rules = rules()
        else:
            self.rules = pyrules
        ##What is a tab (same as rules)
        self.tab = str(tab)
        self.rules.tab = self.tab
        ##Reference to C header file
        self.cheader = cheaderfile
        ##Namespace for code
        self.namespace = "vigil"

    def get_typename(self, member):
        """Get typename of member
        """
        if (isinstance(member, cheader.cstruct)):
            return self.get_name(member)
        elif (isinstance(member, cheader.carray)):
            if (member.object.typename == "char"):
                return "std::string"
            else:
                return self.get_typename(member.object)+"[]"
        else:
            return member.typename

    def get_name(self, struct_in):
        """Get name for struct
        """
        return "of_"+struct_in.typename[4:]

    def ccode(self, preamble=None, preaddon=None, postaddon=None):
        """Return c code
        """
        code = []
        if (preaddon != None):
            code.extend(preaddon)
        if (preamble != None):
            fileRef = open(preamble,"r")
            for l in fileRef:
                code.append(l[:-1])
            fileRef.close()
        if (postaddon != None):
            code.extend(postaddon)

        #Actual code
        code.append("")
        code.append("namespace "+self.namespace)
        code.append("{")
        for name,struct in self.cheader.structs.items():
            code.extend(self.code_struct(struct,True))
        code.append("}")
        return code

    def hcode(self, name="openflow-pack", preamble=None, preaddon=None, postaddon=None):
        """Return code for header
        """
        code = []
        if (preaddon != None):
            code.extend(preaddon)
        if (preamble != None):
            fileRef = open(preamble,"r")
            for l in fileRef:
                code.append(l[:-1])
            fileRef.close()
        if (postaddon != None):
            code.extend(postaddon)
        
        #Code namespace
        code.append("")
        code.append("#ifndef "+name.upper().replace(" ","_").replace("-","_")+"_H")
        code.append("#define "+name.upper().replace(" ","_").replace("-","_")+"_H")
        code.append("")
        code.append("namespace "+self.namespace)
        code.append("{")
        #Code struct
        delayed=[]
        coded=[]
        for name,struct in self.cheader.structs.items():
            if (self.__cancode(struct, coded)):
                code.extend(self.code_struct(struct,False))
                coded.append(struct.typename)
            else:
                delayed.append(struct)
            code.append("")

        delayedagain = []
        while (len(delayed) != 0):
            print "Running another pass on coding header"
            for struct in delayed:
                if (self.__cancode(struct, coded)):
                    code.extend(self.code_struct(struct,False))
                    coded.append(struct.typename)
                else:
                    delayedagain.append(struct)
                code.append("")
            delayed = delayedagain
            
        code.append("}")
        code.append("#endif")
                    
        return code

    def __cancode(self, struct_in, coded):
        """Check if structure can be coded, i.e., field types resolved
        """
        result = True
        for member in struct_in.members:
            if (isinstance(member, cheader.cstruct) and
                member.typename not in coded):
                result = False
        return result

    def code_struct(self, struct_in, ccode):
        """Return code to wrap struct

        Returns None if struct_in is not cheader.cstruct.
        """
        if (not isinstance(struct_in, cheader.cstruct)):
            return None

        code=[]
        indent = self.tab + self.tab
        code.extend(self.codeheader(struct_in,ccode,True))
        #Public code
        if (not ccode):
            code.append(self.tab+"public:")
        code.extend(self.codemembers(struct_in, ccode))

        code.append(indent+"/** \\brief Empty constructor with default assigned")
        code.append(indent+" */")
        code.extend(self.codeemptyconstructor(struct_in,ccode))
        code.append(indent+"/** \\brief Constructor with every field given")
        code.append(indent+" * ")
        code.append(indent+" * Might be good to assign defaults too?")
        code.append(indent+" */")
        code.extend(self.codeconstructor(struct_in,ccode))
        
        code.append(indent+"/** \\brief Pack OpenFlow messages")
        code.append(indent+" */")
        code.extend(self.codepack(struct_in,ccode))
        code.append(indent+"/** \\brief Unpack OpenFlow messages")
        code.append(indent+" */")
        code.extend(self.codeunpack(struct_in,ccode))

        code.append(indent+"/** \\brief Overload assignment (for cloning)")
        code.append(indent+" */")
        code.extend(self.codeeq(struct_in,ccode))
        code.append(indent+"/** \\brief Overload equivalent (for comparison)")
        code.append(indent+" */")
        code.extend(self.codeequiv(struct_in,ccode))
        #Private code
        if (not ccode):
            code.append(self.tab+"private:")
        code.extend(self.codeheader(struct_in,ccode,False))
        return code

    def codeunpack(self, struct_in, ccode):
        """Code unpack that parse bytes according to format
        """
        code=[]
        ##Indent and public code
        indent =self.tab
        if (not ccode):
            indent += self.tab

        cstr = indent+"void "
        if (ccode):
            cstr += self.get_name(struct_in)+"::"
        cstr += "unpack("+struct_in.typename+"* buffer)"
        if (not ccode):
            cstr += ";"
        code.append(cstr)

        if (ccode):
            code.append(indent+"{")
            for member in struct_in.members:
                if (isinstance(member, cheader.cstruct)):
                    code.append(indent+self.tab+member.name+".unpack(&buffer->"+member.name+");")
                elif (isinstance(member, cheader.cprimitive)):
                    code.append(indent+self.tab+member.name+\
                                " = "+self.__determinentoh(member)+"(buffer->"+member.name+");")
                elif (isinstance(member, cheader.carray)):
                    if (member.object.typename == "char" and member.size != 0):
                        code.append(indent+self.tab+member.name+".assign(buffer->"+\
                                    member.name+");")
                    else:
                        for i in range(0,member.size):
                            if (isinstance(member.object, cheader.cprimitive)):
                                code.append(indent+self.tab+member.name+"["+str(i)+"]"\
                                            " = "+self.__determinehton(member.object)+"(buffer->"+\
                                            member.name+"["+str(i)+"]);")
                            elif (isinstance(member.object, cheader.cstruct)):
                                code.append(indent+self.tab+member.name+\
                                            "["+str(i)+"].unpack(&buffer->"+member.name+\
                                            "["+str(i)+"]);")
                                
            code.append(indent+"}")
        
        code.append("")
        return code

    def codepack(self, struct_in, ccode):
        """Code pack that fill bytes according to format
        """
        code=[]
        ##Indent and public code
        indent =self.tab
        if (not ccode):
            indent += self.tab

        cstr = indent+"void "
        if (ccode):
            cstr += self.get_name(struct_in)+"::"
        cstr += "pack("+struct_in.typename+"* buffer)"
        if (not ccode):
            cstr += ";"
        code.append(cstr)

        if (ccode):
            code.append(indent+"{")
            for member in struct_in.members:
                if (isinstance(member, cheader.cstruct)):
                    code.append(indent+self.tab+member.name+".pack(&buffer->"+member.name+");")
                elif (isinstance(member, cheader.cprimitive)):
                    code.append(indent+self.tab+"buffer->"+member.name+\
                                " = "+self.__determinehton(member)+"("+member.name+");")
                elif (isinstance(member, cheader.carray)):
                    if (member.object.typename == "char" and member.size != 0):
                        code.append(indent+self.tab+"strncpy(buffer->"+\
                                    member.name+","+member.name+".c_str(),"+\
                                    str(member.size-1)+");")
                        code.append(indent+self.tab+"buffer->"+member.name+"["+\
                                    str(member.size-1)+"] = '\\0';")
                    else:
                        for i in range(0,member.size):
                            if (isinstance(member.object, cheader.cprimitive)):
                                code.append(indent+self.tab+"buffer->"+member.name+"["+str(i)+"]"\
                                            " = "+self.__determinehton(member.object)+"("+\
                                            member.name+"["+str(i)+"]);")
                            elif (isinstance(member.object, cheader.cstruct)):
                                code.append(indent+self.tab+member.name+\
                                            "["+str(i)+"].pack(&buffer->"+member.name+\
                                            "["+str(i)+"]);")
                                
            code.append(indent+"}")
        
        code.append("")
        return code

    def __determinehton(self,struct_in):
        """Determine htonx

        Return None if not cprimitive
        """
        if (not isinstance(struct_in, cheader.cprimitive)):
            return None

        r = self.__determineprimtype(struct_in)
        if (r == ""):
            return r
        else:
            return "hton"+r

    def __determinentoh(self,struct_in):
        """Determine htonx

        Return None if not cprimitive
        """
        if (not isinstance(struct_in, cheader.cprimitive)):
            return None
        r = self.__determineprimtype(struct_in)
        if (r == ""):
            return r
        else:
            return "ntoh"+r

    def __determineprimtype(self, cprim):
        """Determine cprimitive type
        """
        if (cprim.typename == "short" or
            cprim.typename == "unsigned short" or
            cprim.typename == "uint16_t"):
            return "s"

        if (cprim.typename == "long" or
            cprim.typename == "unsigned long" or
            cprim.typename == "uint32_t"):
            return "l"

        if (cprim.typename == "long long" or
            cprim.typename == "unsigned long long" or
            cprim.typename == "uint64_t"):
            return "ll"
        
        return ""

    def codeeq(self, struct_in, ccode):
        """Overload = for struct
        """
        code=[]
        ##Indent and public code
        indent =self.tab
        if (not ccode):
            indent += self.tab

        cstr = indent+self.get_name(struct_in)+"& "
        if (ccode):
            cstr += self.get_name(struct_in)+"::"
        cstr += "operator=(const "+self.get_name(struct_in)+"& peer_)"
        if (not ccode):
            cstr += ";"
        code.append(cstr)

        if (ccode):
            code.append(indent+"{")
            for member in struct_in.members:
                if (isinstance(member, cheader.carray) and
                    (not member.object.typename == "char")):
                    for i in range(0, member.size):
                        code.append(indent+self.tab+member.name +\
                                    "["+str(i)+"] = peer_." + member.name+"["+str(i)+"];")
                else:
                    code.append(indent+self.tab+member.name +\
                                " = peer_." + member.name+";")
            code.append(indent+self.tab+"return *this;")
            code.append(indent+"}")
        
        code.append("")
        return code

    def codeequiv(self, struct_in, ccode):
        """Overload eq for struct
        """
        code=[]
        ##Indent and public code
        indent =self.tab
        if (not ccode):
            indent += self.tab

        cstr = indent+"bool "
        if (ccode):
            cstr += self.get_name(struct_in)+"::"
        cstr += "operator==(const "+self.get_name(struct_in)+"& peer_) const"
        if (not ccode):
            cstr += ";"
        code.append(cstr)

        if (ccode):
            code.append(indent+"{")
            cstr = indent+self.tab+"return "
            for member in struct_in.members:
                if (isinstance(member, cheader.carray) and
                    (not member.object.typename == "char")):
                    for i in range(0, member.size):
                        cstr += "\\\n"+indent+self.tab+self.tab+\
                                "("+member.name+"["+str(i)+"] == peer_."+\
                                member.name+"["+str(i)+"]) &&"
                else:
                    cstr += "\\\n"+indent+self.tab+self.tab+\
                            "("+member.name+" == peer_."+member.name+") &&"
            code.append(cstr.rstrip("& ")+";")
            code.append(indent+"}")
        
        code.append("")
        return code

    def codeemptyconstructor(self, struct_in, ccode):
        """Code empty constructor of struct
        """
        code=[]
        ##Indent and public code
        indent =self.tab
        if (not ccode):
            indent += self.tab

        ##Simple constructor
        constructstr = indent
        if (ccode):
            constructstr += self.get_name(struct_in)+"::"
        constructstr += self.get_name(struct_in)+"()"
        if (not ccode):
            constructstr += ";"
        code.append(constructstr)

        if (ccode):
            code.append(indent+"{")
            for member in struct_in.members:
                if (isinstance(member, cheader.cprimitive)):
                    code.append(indent+self.tab+member.name+" = "+\
                                str(self.rules.get_default_value(struct_in.typename, member.name))+\
                                ";")
                elif (isinstance(member, cheader.cstruct)):
                    sd = self.rules.get_struct_default(struct_in.typename, member.name)
                    if (sd != None):
                        code.append(indent+self.tab+"(*this)"+sd+";")
                elif (isinstance(member, cheader.carray)):
                    if (member.size != 0 and member.object.typename != "char"):
                        for i in range(0, member.size):
                            if (isinstance(member.object, cheader.cprimitive)):
                                code.append(indent+self.tab+member.name+"["+str(i)+"] = "+\
                                            str(self.rules.get_default_value(member.object.typename, member.name))+\
                                            ";")
                            else:
                                sd = self.rules.get_struct_default(struct_in.typename, member.name)
                                if (sd != None):
                                    code.append(indent+self.tab+member.name+"["+str(i)+"]"+sd+";") 

            code.append(indent+"}")

        code.append("")
        return code
    
    def codeconstructor(self, struct_in, ccode):
        """Code constructor of struct
        """
        code=[]
        ##Indent and public code
        indent =self.tab
        if (not ccode):
            indent += self.tab

        ##Simple constructor
        constructstr = indent
        if (ccode):
            constructstr += self.get_name(struct_in)+"::"
        constructstr += self.get_name(struct_in)+self.codearglist(struct_in)
        if (not ccode):
            constructstr += ";"
        code.append(constructstr)

        if (ccode):
            code.append(indent+"{")
            for member in struct_in.members:
                if (isinstance(member, cheader.carray) and
                    (not member.object.typename == "char")):
                    for i in range(0, member.size):
                        code.append(indent+self.tab+member.name +\
                                    "["+str(i)+"] = " + member.name+"_["+str(i)+"];")
                else:
                    code.append(indent+self.tab+member.name +\
                                " = " + member.name+"_;")
            code.append(indent+"}")

        code.append("")
        return code

    def codearglist(self, struct_in):
        """Code list of arguments
        """
        constructstr = "("
        #Include each member (always ignore zero size array)
        for member in struct_in.members:
            if (isinstance(member, cheader.carray)):
                if (member.size != 0):
                    if (member.object.typename == "char"):
                        constructstr += "std::string " + member.name+"_, "
                    else:
                        constructstr += self.get_typename(member.object) + " " + member.name+"_[], "
            else:
                constructstr += self.get_typename(member) + " " + member.name+"_, "
        constructstr = constructstr.rstrip(", ")+")"
        return constructstr

    def codemembers(self, struct_in, ccode):
        """Code members of struct
        """
        code = []
        indent = self.tab+self.tab

        if (not ccode):
            for member in struct_in.members:
                if (isinstance(member, cheader.carray) and
                    member.size != 0 and
                    member.object.typename == "char"):
                    code.append(indent+"std::string "+member.name+";")
                if (isinstance(member, cheader.cstruct)):
                    code.append(indent+self.get_typename(member)+" "+member.name+";");
        code.append("")
        return code

    def codeheader(self, struct_in, ccode,start=True):
        """Code header of struct
        """
        authors = ""
        if (os.path.isfile("AUTHORS")):
            fileRef = open("AUTHORS", "r")
            for line in fileRef:
                authors += line.strip()+","
            fileRef.close()
        if (len(authors) > 0):
            authors = " [by "+authors.rstrip(",")+"]"
        
        code=[]
        indent = self.tab
        if (not ccode):
            if (start):
                code.append(indent+"/** \\brief Object wrapper for struct "+\
                            struct_in.typename)
                code.append(indent+" *")
                code.append(indent+" * Everything should be in host order.  Only when the packet")
                code.append(indent+" * is packed, it will be done in network order.  So, all byte")
                code.append(indent+" * order translation is done by this library and no one else.")
                code.append(indent+" * ")
                code.append(indent+" * @author pylibopenflow"+authors)
                code.append(indent+" * @date "+datetime.date.today().ctime())
                code.append(indent+" */")
                code.append(indent+"struct "+self.get_name(struct_in))
                code.append(indent+self.tab+": public "+struct_in.typename+"")
                code.append(indent+"{")
            else:
                code.append(indent+"};")
        return code
