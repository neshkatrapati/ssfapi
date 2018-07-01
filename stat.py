from common import *
import math
import logging,pprint
import anydbm



class Constants(object):
    class Vectorizer(object):
        mode_unigrams = "unigrams"
        mode_multigrams = "multigrams"
    class Strings(object):
        @staticmethod
        def exception_log_message(method,exception,message):
            return "{exception} from {method}, message : {message} ".format(exception = exception,method = method, message = message)
    class Context(object):
        mode_binary = "binary"
        mode_frequency = "frequency"
        display_mode_default = "def"

class FeatureIndexException(Exception):
    def __init__(self,location = ""):
        self.location = location
    def __str__(self):
        return "Feature Index Overflow/Underflow at {location}".format(location = self.location)

class Vector(object):
    def __init__(self,id = 0,vector = "",count = 0,context = None):
        """
        :rtype : object
        """
        self.id = id;
        self.vector = vector
        self.count = count
        self.context = Context(self)

    @staticmethod
    def from_string(string):
        s = string.split("\t")
        v = Vector()
        if len(s) != 1:
            v.id = s[0]
            v.vector = s[1]
            v.count = int(s[2])
            v.context = Context.from_string(v, s[3])
        else: 
            v.id = 0 
            v.vector = ""
            v.count = 1
            v.context = Context(v)
        return v

    def d(self):
        """
        :rtype: str
        """
        if type(self.vector) is not tuple:
            return "{id}\t{vector}\t{count}\t{context}".format(id = self.id,vector = self.vector, count = self.count, context = self.context.d())
        else:
            return "{id}\t{vector}\t{count}\t{context}".format(id = self.id,vector = ";".join(self.vector), count = self.count, context = self.context.d())

    def __str__(self):
        """
        :rtype: str
        """
        return self.d()



class Context(object):
    def __init__(self,vector,mode=Constants.Context.mode_binary):
        self.items = {}
        self.mode = mode
        self.vector = vector

    def add(self,item):
        if self.mode == Constants.Context.mode_binary:
            if item not in self.items:
                self.items[item] = 1
        else:
            if item not in self.items:
                self.items[item] = 0
            self.items[item] += 1

    def add_all(self,items):
        for item in items:
            self.add(item)

    @staticmethod
    def from_string(vector, string):
        c = Context(vector)
        s = string.split(";")
        c.add_all(s)
        return c


    def d(self,mode = Constants.Context.display_mode_default):
        if mode == Constants.Context.display_mode_default:
            return ";".join(self.items.keys())

    def get_expanded_context(self,unigrams):
        items = {unigrams[i].id :1 if unigrams[i].id in self.items.keys() else 0 for i in unigrams}
        c = Context(self.vector)
        c.items = items
        return c


    def get_cosine_similarity(self,context):
        p = 0
        sa= 0
        sb= 0
        a = self.values()
        b = context.values()
        for i in range(len(a)):
            p += a[i] * b[i]
            sa += a[i]
            sb += b[i]
            #s += (a[i] - b[i])**2
        s = (sa**0.5) * (sb**0.5)
        return p/s


    def values(self):
        return self.items.values()


    @staticmethod
    def get_context_slice(lines,li,window,n = 1):
        len_lines = len(lines)
        lli = li - n + 1 if li - n  + 1 >=0 else 0
        possible_left_bound = lli - window
        possible_right_bound = li + window
        left_bound = possible_left_bound if possible_left_bound >=0 else 0
        right_bound = possible_right_bound if possible_right_bound < len_lines else len_lines
        context_slice = lines[left_bound:lli] + lines[li+1:right_bound+1]
        return context_slice


class VectorFilter(object):
    def filter(self,pair):
        return True

class ExceptionalVectorFilter(VectorFilter):
    def __init__(self):
        self.pos_classes = ["SYM"]
        self.ex_list = [" "]
    def filter(self,pair):
        for item in pair:
            if type(item) == "str":
                print item
            if ( item.morph.root in self.ex_list ) or (item.tag in self.pos_classes):
                return False
        return True

class VectorFeatures(object):
    """
    A Class containing all the feature vector extracting methods
    """
    @staticmethod
    def unigram_vector_feature(lines,li,dummy = None):
        """
        Returns the root of the line specified by the index.
        :rtype: str
        """
        return lines[li].morph.root

    @staticmethod
    def unigram_word_feature(lines,li,dummy = None):
        """
        Returns the root of the line specified by the index.
        :rtype: str
        """
        return lines[li].word

    @staticmethod
    def bigram_vector_feature(lines,li,vector_filter = VectorFilter()):
        if li-1 >= 0:
            right = lines[li]
            for l in range(li)[::-1]:
                left = lines[l]
                status = vector_filter.filter((right, left))
                if status == True:
                    return (left.morph.root,right.morph.root)
            raise FeatureIndexException("Bigram Feature Vector Extractor")
        else:
            raise FeatureIndexException("Bigram Feature Vector Extractor")


    @staticmethod
    def ngram_decorator(n):
        """
        Returns a function given n.
        """
        def ngram_vector_feature(lines,li,vector_filter = None):
            lb = li - n + 1 if li - n + 1 >= 0 else 0
            plb = li -n +1
            if plb < 0:
                raise FeatureIndexException("{n}-gram Feature Vector Extractor".format(n=n))
            else:
                right = lines[li]
                r = [right]
                for l in range(li)[::-1]:
                    left = lines[l]
                    status = vector_filter.filter(tuple( r + [left] ))
                    if status == True:
                        r.insert(0,left.morph.root)
                    if len(r) == n:
                        r[-1] = r[-1].morph.root
                        return tuple(r)
                raise FeatureIndexException("Bigram Feature Vector Extractor")
                # r = [line.morph.root for line in lines[lb:li+1]]
                # return tuple(r)
        return ngram_vector_feature



class Vectorizer(object):

    def __init__(self, corpus, filename):
        self.corpus = corpus
        #self.vectors = shelve.open(filename,writeback=True)

    @staticmethod
    def from_file(filename,mode = Constants.Vectorizer.mode_unigrams):
        vectors = {}
        with open(filename) as f:
            for line in f.readlines():
                line = line.strip("\n\t ")
                line = line.split("\t")

                vector = Vector()
                vector.id  = line[0]
                if mode == Constants.Vectorizer.mode_unigrams:
                    vector.vector = line[1]
                else:
                    vector.vector = tuple(line[1].split(";"))
                vector.count = line[2]
                vector.context = Context(vector)
                if len(line) == 4:
                    vector.context.add_all(line[3].split(";"))
                    vectors[vector.vector] = vector
            v = Vectorizer(None)
            v.vectors = vectors
            return v


    def vectorize(self,vector_feature,window = 2,mode = Constants.Vectorizer.mode_unigrams,n = 1,vector_filter = VectorFilter(), filename = ""):
        """
        Prepares vectors, given the appropriate feature function
        """

        #vectors = self.vectors
        vectors = anydbm.open(filename, 'c')
        #vector_id = len(self.vectors)
        vector_id = 1
        for sentence in self.corpus:
            nsent = SSFUtils.remove_chunks(sentence)
            #if mode == Constants.Vectorizer.mode_multigrams:
            #    nsent.d(SSFSentence.display_mode_flat)
            lines = nsent.lines()
            len_lines = len(lines)
            for li in range(len(lines)):
                line = lines[li]
                try:
                    vector = vector_feature(lines,li,vector_filter) # Call the Feature function
                    vrep = ";".join(vector)

                    if vrep not in vectors:
                        #vectors[vrep] = Vector(id = vector_id,vector = vector)
                        vectors[vrep] = ""
                        vector_id += 1

                    # Computing Context Bounds
                    context_slice = Context.get_context_slice(lines,li,window,n)
                    #context_slice = [VectorFeatures.unigram_vector_feature(context_slice,l) for l in range(len(context_slice))]
                    context_slice = [VectorFeatures.unigram_word_feature(context_slice,l) for l in range(len(context_slice))]

                    vector_back = Vector.from_string(vectors[vrep])
                    vector_back.count += 1
                    vector_back.context.add_all(context_slice)
                    vectors[vrep] = vector_back.d()
                    #vectors[vrep].count += 1

                    #vectors[vrep].context.add_all(context_slice)

                    #if mode == Constants.Vectorizer.mode_multigrams:
                        #print vectors[vector]

                except FeatureIndexException as e:
                    pass
                    #logging.exception(Constants.Strings.exception_log_message("Vectorizer.vectorize",FeatureIndexException,"")
            
        self.vectors = vectors

        logging.info("{n} Vectors".format(n = str(len(self.vectors))))
        self.vectors.close()

    def convert_context_into_numbers(self,mode = Constants.Vectorizer.mode_unigrams,filename=None):
        # Converting context strings to indices.
        vectors = self.vectors
        if mode == Constants.Vectorizer.mode_unigrams:
            # Incase the mode is unigram vectorization, the unigrams are already in the vectors variable
            unigram_vectors = vectors
        elif filename != None:
            unigram_vectors = shelve.open(filename)

        
        for vector in vectors:
            # if mode == Constants.Vectorizer.mode_unigrams:
            #     print vector,vectors[vector].context.items
            context = Context(vectors[vector].vector)
            context_slice = [ str(unigram_vectors[item].id) for item in vectors[vector].context.items ] # This part needs Unigram vectors.
            context.add_all(context_slice)
            vectors[vector].context = context

        self.vectors = vectors

    def save(self):
        self.vectors.close()

    def write_to_file(self,filename):
        with open(filename,"w") as w:
            for vector in self.vectors:
                w.write(self.vectors[vector].d() + "\n")

    def save_all_to_db(self, cursor):
        pass

# class SQLiteWrapper(object):
#     def __init__(self,dbname):
#         self.conn = sqlite3.connect(dbname)

#     def get_index(self,vector,tablename):
#         c = self.conn.cursor()
#         query = "SELECT id from {tablename} where vector=\'{vector}\'".format(**locals())
#         result = c.execute(query)
#         row = c.fetchone()
#         return row[0]


#     def get_unigram_index(self,vector):
#         return self.get_index(vector,"unigrams")
