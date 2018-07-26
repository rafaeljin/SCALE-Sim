import os.path
import math
import collections

def prune(input_list):
    l = []
    for e in input_list:
        e = e.strip()
        if e != '' and e != ' ':
            l.append(e)
    return l

def parse_input (line,min_addr,max_addr):
    elems = line.strip().split(',')
    elems = prune(elems)
    elems = [float(x) for x in elems]
    clk = elems[0]
    # get valid elements
    elems = elems[1:]
    elems = [x for x in elems if x >= min_addr and x < max_addr]
    return clk, elems

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

# first implementation, stalling whenever it is necessary
def dram_trace_limited_v1(
        sram_sz         = 512 * 1024,
        word_sz_bytes   = 1,
        min_addr = 0, max_addr=1000000,
        max_bw = 1,               
        sram_trace_file = "sram_log.csv",
        dram_trace_file = "dram_log.csv"
    ):

    res = -1 
    sram = FIFO_mem(sram_sz) 

    sram_requests = open(sram_trace_file, 'r')
    dram          = open(dram_trace_file, 'w')

    total_stalls,extras_slots = 1, 0

    for entry in sram_requests:

        clk, elems = parse_input(entry,min_addr,max_addr) 

        if len(elems) == 0 and res == -1: 
            res = total_stalls 
        free_reads = extras_slots + max_bw
        stalls = 0

        for e in elems:
            
            if not sram.check(e) and e >= min_addr and e < max_addr:
                if free_reads == 0:
                    free_reads = max_bw
                    total_stalls += 1
                    stalls += 1
                free_reads -= 1
                sram.use(e)

        extras_slots = free_reads

        trace = str(int(clk)) + " use " + str(int(stalls)) + "\n"
        dram.write(trace)


    trace = "total stalls: " + str(total_stalls)
    dram.write(trace)

    sram_requests.close()
    dram.close()
    return total_stalls, res

def dram_trace_limited_v2(
        sram_sz         = 512 * 1024,
        word_sz_bytes   = 1,
        min_addr = 0, max_addr=1000000,
        max_bw = 1,               
        max_pure_read_cycles = 1,               
        penalty = 0,
        sram_trace_file = "sram_log.csv",
        dram_trace_file = "dram_log.csv"
    ):

    debug_mode = False 

    sram2 = ideal_mem(sram_sz) 

    sram_requests = open(sram_trace_file, 'r')
    dram          = open(dram_trace_file, 'w')
    
    # buffer to slide window
    sram_buffer = []
    for entry in sram_requests:
        sram_buffer.append(entry)
    sram_requests.close()
    
    stalls = 0

    # read: cycle data into read_buffer, run: attempting cycle
    read, run= -1, 0 
    # read, run cycle
    read_c, run_c = 0, 0
    read_buffer, run_buffer = [], []

    while run < len(sram_buffer):

        if debug_mode:
            print "read"
        # read
        read_stall = 0
        max_number_of_reads = max_pure_read_cycles * max_bw
        while True:
            if len(read_buffer) == 0:
                read += 1
                if read >= len(sram_buffer):
                    break
                read_c, read_buffer = parse_input(sram_buffer[read],min_addr,max_addr)

            read_stall += max_number_of_reads
            max_number_of_reads,read_buffer = sram2.read(read_buffer,read_c,max_number_of_reads)
            # sram full
            read_stall -= max_number_of_reads
            # 2 possible break conditions: read buffer not cleared (mem full) 
            # or max pure read cycles used up 
            if len(read_buffer) != 0:
                break
        if debug_mode:
            print read_c 
        cycle_stalls = (read_stall+max_bw-1)/max_bw
        stalls += cycle_stalls
        # trace = str(int(run_c)) + " use " + str(int(cycle_stalls)) + "\n"
        # dram.write(trace)

        if debug_mode:
            print "exe"
        # execute
        while True:
            if run == len(sram_buffer):
                break
            run_c, run_buffer = parse_input(sram_buffer[run],min_addr,max_addr)
            # end of one batch
            if len(run_buffer) == 0:
                run += 1
                break
            res = sram2.run(run_buffer,run_c)
            if not res:
                dram.write("penalty at " + str(run_c) + "of " + str(penalty) + " cycles\n")
                stalls += penalty
                break
            else:
                run += 1
            # read while running 
            number_of_reads = max_bw
            while True:
                if len(read_buffer) == 0:
                    read += 1
                    if read < len(sram_buffer):
                        read_c, read_buffer = parse_input(sram_buffer[read],min_addr,max_addr)
                    # if read to the end
                    else:
                        break
                number_of_reads, read_buffer = sram2.read(read_buffer,read_c,number_of_reads)
                # no more free bandwidth in this cycle
                if len(read_buffer) != 0:
                    break
        if debug_mode:
            print run_c

    trace = "total stalls: " + str(stalls)
    dram.write(trace)
    dram.close()
    return stalls

def dram_trace_limited(
        sram_szs         = [512 * 1024],
        word_sz_bytes   = 1,
        min_addr = 0, max_addr=1000000,
        max_bws = [1],               
        penalty = 0,               
        sram_trace_file = "sram_log.csv",
        dram_trace_file = "dram_log.csv"
    ):

    for max_bw in max_bws:
        print "max_bw = " + str(max_bw)
        for sram_sz in sram_szs:
            print "\tsram_sz = " + str(sram_sz)
            stalls, max_pure_read_cycles = dram_trace_limited_v1(sram_sz,word_sz_bytes,min_addr,max_addr,max_bw,sram_trace_file,"first_method"+dram_trace_file)
            print "\t\tfirst method " + str(stalls)
            print "\t\tmax pure cyles:"+ str(max_pure_read_cycles)
            stalls = dram_trace_limited_v2(sram_sz,word_sz_bytes,min_addr, max_addr, max_bw, max_pure_read_cycles, penalty, sram_trace_file,"second_method"+dram_trace_file)
            print "\t\tsecond method" + str(stalls)

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
