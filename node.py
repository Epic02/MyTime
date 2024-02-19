class Node:
    def __init__(self):
        self.name = ""
        self.outname = ""
        self.Cload = 0.0
        self.inputs = [] #list of handles to the fanin nodes of this node
        self.outputs =[] #list of handles to the fanout nodes of this node
        self.Tau_in = [] # array/list of input slews (for all inputs tothe gate), to be used for STA
        self.inp_arrival = [] # array/list of input arrival times for input transitions (ignore rise or fall)
        self.outp_arrival = [] # array/list of output arrival times, outp_arrival = inp_arrival + cell_delay
        self.max_out_arrival = 0.0 # arrival time at the output of this gate using max on (inp_arrival +cell_delay)
        self.Tau_out = 0.0 # Resulting output slew
        self.visit_count = 0
        self.inp_count = 0
        self.all_inp_vstd=False