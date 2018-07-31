import os.path
import math
import collections
from memory_models import FIFO_mem
from memory_models import ideal_mem 

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
            print "read======================================"
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
            print sram2.last_used.keys() #read_c 
        cycle_stalls = (read_stall+max_bw-1)/max_bw
        stalls += cycle_stalls
        # trace = str(int(run_c)) + " use " + str(int(cycle_stalls)) + "\n"
        # dram.write(trace)

        if debug_mode:
            print "exe======================================="
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
            if debug_mode:
                print "run:" + str(run_c)
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
                print sram2.last_used.keys()
        if debug_mode:
            print ""#run_c

    trace = "total stalls: " + str(stalls)
    dram.write(trace)
    dram.close()
    return stalls


def dram_trace_limited_v3(
        sram_sz         = 512 * 1024,
        word_sz_bytes   = 1,
        min_addr = 0, max_addr=1000000,
        max_bw = 1,               
        max_pure_read_cycles = 1,               
        array_width = 4,
        num_filters = 1,
        filter_size = 10,
        sram_trace_file = "sram_log.csv",
        dram_trace_file = "dram_log.csv"
    ):

    debug_mode = False 

    sram3 = ideal_mem(sram_sz) 

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
    first_set_of_filters = True

    while run < len(sram_buffer):

        if debug_mode:
            print "read======================================"
        # read
        read_stall = 0
        if first_set_of_filters:
            read_cycles = max_pure_read_cycles
            #print ("f",num_filters)
            num_filters -= array_width
            first_set_of_filters = False
        else:
            # NF/b - (F+N-1-(b+1)/2)
            N = min(num_filters,array_width)
            #print ('N',N)
            num_filters -= array_width
            read_cycles = (N*filter_size+max_bw-1)/max_bw - (N+filter_size-1-(max_bw+1)/2) 
        max_number_of_reads = read_cycles * max_bw

        while True:
            if len(read_buffer) == 0:
                read += 1
                if read >= len(sram_buffer):
                    break
                read_c, read_buffer = parse_input(sram_buffer[read],min_addr,max_addr)

            read_stall += max_number_of_reads
            max_number_of_reads,read_buffer = sram3.read(read_buffer,read_c,max_number_of_reads)
            # sram full
            read_stall -= max_number_of_reads
            # 2 possible break conditions: read buffer not cleared (mem full) 
            # or max pure read cycles used up 
            if len(read_buffer) != 0:
                break
        if debug_mode:
            print read_c#sram3.last_used.keys() 
        cycle_stalls = (read_stall+max_bw-1)/max_bw
        stalls += cycle_stalls
        # trace = str(int(run_c)) + " use " + str(int(cycle_stalls)) + "\n"
        # dram.write(trace)

        if debug_mode:
            print "exe======================================="
        # execute
        while True:
            if run == len(sram_buffer):
                break
            run_c, run_buffer = parse_input(sram_buffer[run],min_addr,max_addr)
            # end of one batch
            if len(run_buffer) == 0:
                run += 1
                break
            res = sram3.run(run_buffer,run_c)
            if not res:
                print "error! penalty caused"
                break
            else:
                run += 1
            if debug_mode:
                a = 1#print "run:" + str(run_c)
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
                number_of_reads, read_buffer = sram3.read(read_buffer,read_c,number_of_reads)
                # no more free bandwidth in this cycle
                if len(read_buffer) != 0:
                    break
            if debug_mode:
                a = 1#print ""#sram3.last_used.keys()
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
        array_w = 1,
        num_filt = 1,
        filter_size = 1,
        sram_trace_file = "sram_log.csv",
        dram_trace_file = "dram_log.csv"
    ):

    for max_bw in max_bws:
        bw_res = []
        print "max_bw = " + str(max_bw)
        repeat,lastvalue = False, -1
        for sram_sz in sram_szs:
            print "\tsram_sz = " + str(sram_sz)
            if not repeat:
                stalls, max_pure_read_cycles = dram_trace_limited_v1(sram_sz,word_sz_bytes,min_addr,max_addr,max_bw,sram_trace_file,"first_method"+dram_trace_file)
            print "\t\tfirst method " + str(stalls)
            print "\t\tmax pure cyles:"+ str(max_pure_read_cycles)
            if not repeat:
                stalls = dram_trace_limited_v2(sram_sz,word_sz_bytes,min_addr, max_addr, max_bw, max_pure_read_cycles, penalty, sram_trace_file,"second_method"+dram_trace_file)
            print "\t\tsecond method " + str(stalls)
            if stalls == lastvalue:
                repeat = True
            lastvalue = stalls
            bw_res.append(stalls)

            #print("fiii",num_filt)
            #print("w",array_w)
            #print("fs",filter_size)
            stalls = dram_trace_limited_v3(sram_sz,word_sz_bytes,min_addr, max_addr, max_bw, max_pure_read_cycles, array_w, num_filt, filter_size, sram_trace_file,"third_method"+dram_trace_file)
            print "\t\tthird method " + str(stalls)
        print bw_res

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
