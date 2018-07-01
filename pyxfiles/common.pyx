import re
import pprint
import sys


class MorphStructure(object):
    """ A Class to represent Morph Feature Structure """
    def __init__(self,fs_string):
        """ Basic Initialization Method """
        self.fs_string = fs_string
        self.fs = None

    @staticmethod
    def from_string(fs_string):
        """ Returns a MorphStructure Object from the string """
        mo = MorphStructure(fs_string)
        mo.process()
        return mo
    
    def process(self):
        """ Processes The Feature Structure Into a Dict """
        t = self.fs_string.strip("<>").split(" ")
        self.fs = {"af" : ["NA"]} # This is a patch ! Investigate 
        for ts in t[1:]:
            if ts not in [""," ","\n","\t"]:
                tx = ts.split("=")
                if "," in tx[1]:
                    self.fs[tx[0]] = tx[1].strip("'").split(",")
                else:
                    self.fs[tx[0]] = tx[1].strip("'")

    @property
    def root(self):
        """ Get the root of the word """ 
        return self.fs["af"][0]
     
    def __str__(self):
        return self.fs_string # Temporary
        
    def d(self):
        pprint.pprint( self.fs )

class SSFPropertyOverflow(Exception):
    def __init__(self,property):
        self.property = property
    def __str__(self):
        return "{0} Property Not Found in the Line".format(self.property)


class SSFLine(object):
    """ Represents Each Line of an SSF Sentence """
    # Inherit this for SSF Chunk etc.
    def __init__(self,line):
        """ Initialize from String """
        self.line = line.split("\t")
        
    @property
    def index(self):
        if len(self.line) > 0:
            return self.line[0]
        else: 
            raise SSFPropertyOverflow("index") # Replace with constants
    
    @property
    def word(self):
        if len(self.line) > 1:
            return self.line[1]
        else: 
            raise SSFPropertyOverflow("word") # Replace with constants

    @property
    def tag(self):
        if len(self.line) > 2:
            return self.line[2]
        else: 
            raise SSFPropertyOverflow("tag") # Replace with constants
    
    @property
    def morph(self):
        if len(self.line) > 3:
            return MorphStructure.from_string(self.line[3])
        else: 
            raise SSFPropertyOverflow("morph") # Replace with constants

    def d(self,seperator = "\t"):
        return seperator.join(self.line)

    def __str__(self):
        return self.d()
    
    
    
class SSF(object):
    def __init__(self,ssf):
        self.ssf = ssf
        self.current = 0 # Used in Iterators

    @staticmethod
    def from_file(filename):
        """ Reads from File and Returns a New SSF Object """
        ssf = open(filename).read()
        ssfo =  SSF(ssf)
        ssfo._sentences()
        return ssfo
    
    def _sentences(self):
        """ Processes Sentences """
        sentence_tag_regex = re.compile('<Sentence[\s\S]*?</Sentence>\n')
        sentences = re.findall(sentence_tag_regex,self.ssf)
        self.sentence_list = [ SSFSentence.from_string(sentence) for sentence in sentences ]

    def sentences(self):
        """ Returns Sentences """
        return self.sentence_list

    def __iter__(self):
        return self

    def next(self):
        """ Iterator for the sentences """
        if self.current < len(self.sentence_list):
            self.current += 1
            return self.sentence_list[self.current - 1]
        else: 
            self.current = 0
            raise StopIteration

    def __str__(self):
        """ The tostring method """
        return "{0} Sentences".format(len(self.sentence_list))

class SSFSentence(object):
    """ Represents a Sentence """

    display_mode_full = "full"
    display_mode_flat = "flat"
    display_mode_pos = "pos"
    chunk_markers = ["((","))"]
    word_mode_wordform = "wordform"
    word_mode_root = "root"

    def __init__(self, ssf):
        self.ssf = ssf
    

    @staticmethod
    def from_string(sentence):
        ssfso  = SSFSentence(sentence)
        ssfso._lines()
        return ssfso

    @staticmethod
    def from_lines(lines):
        ssfso = SSFSentence("")
        i = 1
        e = [0]
        for line in lines:
            if len(e) <= 1:
                e[0]  = str(i)

            index = e[0]

            if line.word == "((":
                e.append(str(1))
            elif line.word == "))":
                e = e[:-1]
                e[0] = str(int(e[0]) + 1)
                index = ""
            else:
                if len(e) > 1:
                    index += "." + ".".join(e[1:])
                    e[-1] = str(int(e[-1]) + 1)

            line.line[0] = index
            i+= 1
        ssfso.line_list = lines
        return ssfso 

    def _lines(self):
        """ Processes all Lines """        
        self.line_list = [SSFLine(line) for line in  self.ssf.split("\n") if (line.strip("\n\t ").startswith("<") == False) and (len(line) > 2)]

    def lines(self):
        """ Returns all Lines """
        return self.line_list

    def __str__(self):
        return "{0} Lines".format(len(self.line_list))
 
    def d(self,mode = display_mode_full,word_mode = word_mode_wordform):
        if mode == SSFSentence.display_mode_full:
            print "<Sentence id=1>"
            for line in self.lines():
                print line
            print "</Sentence>"
        elif mode in [SSFSentence.display_mode_flat,SSFSentence.display_mode_pos]:
            for line in self.lines():
                if line.word in SSFSentence.chunk_markers:
                    print line.word,
                else:
                    extra = ""
                    if mode == SSFSentence.display_mode_pos:
                        extra = "/{pos}".format(pos = line.tag)

                    if word_mode == SSFSentence.word_mode_wordform:
                        print line.word+extra,
                    else:
                        print line.morph.root+extra,

            print ""


class SSFUtils(object):
    """ A Mix of all the SSF Utilities """
    @staticmethod
    def remove_chunks(ssfsentence):
        """ Removes chunk information if any and returns a new SSF"""
        # TODO Think About indices
        lines = ssfsentence.lines()
        new_lines = []
        for l in range(len(lines)):
            line = lines[l]
            if line.word not in ["((","))"]:
                new_lines.append(line)
        return SSFSentence.from_lines(new_lines)


