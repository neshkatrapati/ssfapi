from common import *

import sys 

import time

start = time.time()
print "Started Program"

ssf_file = sys.argv[1]


ssf = SSF.from_file(ssf_file)

e1 = time.time()


for sentence in ssf.sentences()[:100]:
    nsent = SSFUtils.remove_chunks(sentence)
    print nsent.d(ignore_pos = True)

end = time.time()
print "Imported SSF File : ", e1 - start
print "Done : ", end - e1
