import math
import collections

class FIFO_mem:

    def __init__(self,n):
        self.size = n
        self.elems = set()
        self.q = collections.deque(maxlen = n)

    # check whether i is in memory
    def check(self,i):
        if i in self.elems: # not in mem
            return True
        else:
            return False

    # put element into memory, return replaced element (if occurs)
    def use(self,i):
        ret = -1
        if i not in self.elems: # not in mem
            if len(self.elems) >= self.size:
                ret = self.q.popleft()
                self.elems.remove(ret)
            self.q.append(i)
            self.elems.add(i)
        return ret

class ideal_mem_v1:

    def __init__(self,n):
        self.size = n
        self.last_used = {} 
        self.current_cycle = 0
        # deque should not have maxlen
        self.freelist = collections.deque()
        # list of elements 
        self.l = [] 

    def check (self,ele):
        if ele in self.last_used:
            return True
        else:
            return False

    def debug(self):
        print ("used:",len(self.last_used))
        print self.last_used 
        print ("l",self.l)
        print ("cycle", self.current_cycle)
        print ("freelist", self.freelist)
        print ""

    # elems required at cycle 
    def read (self, elems, cycle_number, max_number_of_reads):
        #print "read"
        # 3 cases: elems[-1] already in memory OR not in memory and memory not full OR not in memory, memory full but free list available
        # while BASE and (CASE 1 OR (CASE 2 OR CASE 3)), each loop process one element
        while elems and \
                (elems[-1] in self.last_used or \
                        ( (len(self.last_used) < self.size or len(self.freelist) > 0) and max_number_of_reads > 0 ) ):
            # appending execution list for cycle
            while cycle_number-self.current_cycle >= len(self.l):
                self.l.append([])
            # if not in memory, one read required. 
            if elems[-1] not in self.last_used:
                max_number_of_reads -= 1
                # memory fully occupied but some can be replaced 
                if len(self.last_used) == self.size:
                    if len(self.freelist) <= 0:
                        raise Exception("erro aqui")
                    toremove = self.freelist.popleft()
                    if self.last_used[toremove] != -1 :
                        raise Exception("tem um erro aqui")
                    else :
                        del self.last_used[toremove]
            # regular procedure: update last_used, append to l and remove from elems
            self.last_used[elems[-1]] = cycle_number
            if len(self.last_used) > self.size:
                raise Exception("outro erro")
            self.l[-1].append(elems[-1])
            del elems[-1]
            # remove fake freelist entries 
            while len(self.freelist) > 0 and (self.freelist[0] not in self.last_used or (self.last_used[self.freelist[0]] != -1)):
                self.freelist.popleft()
        #self.debug()
        return max_number_of_reads, elems

    def run(self,elems, cycle_number):
        #print "run"
        flag = True

        while len(self.freelist) > 0 and (self.freelist[0] not in self.last_used or (self.last_used[self.freelist[0]] != -1)):
            raise Exception("exquisito denovo")
            self.freelist.popleft()

        for ele in elems:
            if ele not in self.last_used:
                flag = False

        if flag and cycle_number == self.current_cycle and len(self.l) > 0:
            for ele in self.l[0]:
                if self.last_used[ele] == self.current_cycle:
                    self.last_used[ele] = -1
                    self.freelist.append(ele)
            self.current_cycle = self.current_cycle + 1
            del self.l[0]

        while len(self.freelist) > 0 and (self.freelist[0] not in self.last_used or (self.last_used[self.freelist[0]] != -1)):
            if self.freelist[0] not in self.last_used:
                print self.freelist[0]
                raise Exception("exquisito1")
            elif self.last_used[self.freelist[0]] != -1:
                raise Exception("exquisito2")
            raise Exception("exquisito3")
            self.freelist.popleft()

        #self.debug()
        return flag

class ideal_mem:

    def __init__(self,n):
        self.size = n
        self.last_used = {} 
        self.current_cycle = 0
        # deque should not have maxlen
        self.freelist = collections.deque()
        # list of elements 
        self.l = [] 

    def check (self,ele):
        if ele in self.last_used:
            return True
            #return self.last_used[ele]
        else:
            return False

    def debug(self):
        print ("used:",len(self.last_used))
        print self.last_used 
        print ("l",self.l)
        print ("cycle", self.current_cycle)
        print ("freelist", self.freelist)
        print ""

    # elems required at cycle 
    def read (self, elems, cycle_number, max_number_of_reads):
        #print "read"
        # 3 cases: elems[-1] already in memory OR not in memory and memory not full OR not in memory, memory full but free list available
        # while BASE and (CASE 1 OR (CASE 2 OR CASE 3)), each loop process one element
        while elems and \
                (elems[-1] in self.last_used or \
                        ( (len(self.last_used) < self.size or len(self.freelist) > 0) and max_number_of_reads > 0 ) ):
            # appending execution list for cycle
            while cycle_number-self.current_cycle >= len(self.l):
                self.l.append([])
            # if not in memory, one read required. 
            if elems[-1] not in self.last_used:
                max_number_of_reads -= 1
                # memory fully occupied but some can be replaced 
                if len(self.last_used) == self.size:
                    if len(self.freelist) <= 0:
                        raise Exception("erro aqui")
                    toremove = self.freelist.popleft()
                    if self.last_used[toremove] != -1 :
                        raise Exception("tem um erro aqui")
                    else :
                        del self.last_used[toremove]
            # regular procedure: update last_used, append to l and remove from elems
            self.last_used[elems[-1]] = cycle_number
            if len(self.last_used) > self.size:
                raise Exception("outro erro")
            self.l[-1].append(elems[-1])
            del elems[-1]
            # remove fake freelist entries 
            while len(self.freelist) > 0 and (self.freelist[0] not in self.last_used or (self.last_used[self.freelist[0]] != -1)):
                self.freelist.popleft()
        #self.debug()
        return max_number_of_reads, elems

    def run(self,elems, cycle_number):
        #print "run"
        flag = True

        while len(self.freelist) > 0 and (self.freelist[0] not in self.last_used or (self.last_used[self.freelist[0]] != -1)):
            raise Exception("exquisito denovo")
            self.freelist.popleft()

        for ele in elems:
            if ele not in self.last_used:
                flag = False

        if flag and cycle_number == self.current_cycle and len(self.l) > 0:
            for ele in self.l[0]:
                if self.last_used[ele] == self.current_cycle:
                    self.last_used[ele] = -1
                    self.freelist.append(ele)
            self.current_cycle = self.current_cycle + 1
            del self.l[0]

        while len(self.freelist) > 0 and (self.freelist[0] not in self.last_used or (self.last_used[self.freelist[0]] != -1)):
            if self.freelist[0] not in self.last_used:
                print self.freelist[0]
                raise Exception("exquisito1")
            elif self.last_used[self.freelist[0]] != -1:
                raise Exception("exquisito2")
            raise Exception("exquisito3")
            self.freelist.popleft()

        #self.debug()
        return flag

if __name__ == "__main__":
    t = ideal_mem(5)
    t.debug()
    t.read([1,2,3],0,2)
    t.debug()
    t.read([1],0,2)
    t.debug()
    t.read([1],1,2)
    t.debug()
    t.run([1,2,3],0)
