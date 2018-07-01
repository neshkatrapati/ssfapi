from ssfc import *

import sys 

import time

start = time.time()
print "Started Program"

ssf_file = sys.argv[1]
mwdict = sys.argv[2]

ssf = SSF.from_file(ssf_file)

e1 = time.time()

types= {"conjunct-verb":1}

mdict = MWDict.from_file(mwdict,types)
md = MWEDetect(mdict)



for sentence in ssf.sentences()[:100]:
    nsent = SSFUtils.remove_chunks(sentence)
    #md.patch_test_trie(nsent,trie)
    md.detect_contiguous(nsent).d()

    #md.detect_conjunct_verbs(nsent).d(SSFSentence.display_mode_pos)
end = time.time()
print "Imported SSF File : ", e1 - start
print "Done : ", end - e1
