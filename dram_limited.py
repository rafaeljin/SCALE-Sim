import os.path
import math
import queue
from tqdm import tqdm

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
        self.q = queue.Queue(maxsize = n)

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
                ret = self.q.get()
                self.elems.remove(ret)
            self.q.put(i)
            self.elems.add(i)
        return ret

class ideal_mem:

    def __init__(self,n):
        self.size = n
        self.last_used = {} 
        self.current_cycle = 0
        self.freelist = queue.Queue(maxsize = n)
        # list of elements 
        self.l = [] 

    def debug(self):
        print ("used:",len(self.last_used))
        print self.last_used 
        print ("l",self.l)
        print ("cycle", self.current_cycle)
        print ("freelist", list(self.freelist.queue))
        print ""

    # elems required at cycle 
    def read (self, elems, cycle_number, max_number_of_reads):
        print "read"
        while elems and (elems[-1] in self.last_used or \
                ( (len(self.last_used) < self.size or len(freelist) > 0) \
                and max_number_of_reads > 0) ):
            # appending execution list for cycle
            while cycle_number-self.current_cycle >= len(self.l):
                self.l.append([])
            # if not in memory, one quota needed to read 
            if elems[-1] not in self.last_used:
                max_number_of_reads = max_number_of_reads - 1
            # memory fully occupied but some can be replaced 
            if len(self.last_used) == self.size:
                toremove = freelist.get()
                if self.last_used[toremove] != -1 :
                    print "tem um erro aqui"
                else :
                    del self.last_used[toremove]
            # regular procedure 
            self.last_used[elems[-1]] = cycle_number
            self.l[-1].append(elems[-1])
            del elems[-1]
        self.debug()
        return max_number_of_reads, elems

    def run(self,elems, cycle_number):
        print "run"
        flag = True
        for ele in elems:
            if ele not in self.last_used:
                flag = False
        print ('cn',cycle_number,flag)
        if flag and cycle_number == self.current_cycle and len(self.l) > 0:
            for ele in self.l[0]:
                if self.last_used[ele] == self.current_cycle:
                    self.last_used[ele] = -1
                    self.freelist.put(ele)
            self.current_cycle = self.current_cycle + 1
            del self.l[0]
        self.debug()
        return flag


def dram_trace_limited(
        sram_sz         = 512 * 1024,
        word_sz_bytes   = 1,
        min_addr = 0, max_addr=1000000,
        max_bw = 1,               
        sram_trace_file = "sram_log.csv",
        dram_trace_file = "dram_log.csv"
    ):

    sram = FIFO_mem(sram_sz) 

    sram_requests = open(sram_trace_file, 'r')

    total_stalls = 1
    # slot for next clock
    extras_slots = 0

    for entry in sram_requests:

        clk, elems = parse_input(entry,min_addr,max_addr)

        if len(elems) == 0 :
            break

        clk = elems[0]
        #print('clk',int(clk))

        free_reads = extras_slots + max_bw
        #print('free:',free_reads)

        for e in elems:
            
            if (not sram.check(e)) and (e >= min_addr) and (e < max_addr):
                #print ('e',int(elems[e]))
                if free_reads == 0:
                    free_reads = max_bw
                    total_stalls += 1
                free_reads -= 1
                sram.use(e)

        extras_slots = free_reads

    # purpose of first part is generate max pure read cycles
    max_pure_read_cycles = total_stalls
    print (max_pure_read_cycles, "!!!!!!!!!!!")
    sram_requests.close()

    sram2 = ideal_mem(sram_sz) 

    sram_requests = open(sram_trace_file, 'r')
    dram          = open(dram_trace_file, 'w')
    
    # buffer to slide window
    sram_buffer = []
    for entry in sram_requests:
        sram_buffer.append(entry)
    sram_requests.close()
    
    total_stalls = 0

    read, run= -1, 0 
    # read, run cycle
    read_c, run_c = 0, 0
    read_buffer, run_buffer = [], []

    while run < len(sram_buffer):

        print "read"
        # read
        read_stall = 0
        max_number_of_reads = max_pure_read_cycles * max_bw
        while True:
            if len(read_buffer) == 0:
                read = read + 1
                if read == len(sram_buffer):
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

        trace = str(int(run_c)) + " use " + str(int(read_stall/max_bw)) + "\n"
        dram.write(trace)

        print "exe"
        # execute
        while True:
            if run == len(sram_buffer):
                break
            run_c, run_buffer = parse_input(sram_buffer[run],min_addr,max_addr)
            res = sram2.run(run_buffer,run_c)
            print res
            if not res:
                break
            else:
                run = run + 1
            # read while running 
            number_of_reads = max_bw
            while True:
                if len(read_buffer) == 0:
                    read = read + 1
                    if read < len(sram_buffer):
                        read_c, read_buffer = parse_input(sram_buffer[read],min_addr,max_addr)
                    else:
                        break
                number_of_reads, read_buffer = sram2.read(read_buffer,read_c,number_of_reads)
                if len(read_buffer) != 0:
                    break
    dram.close()


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
