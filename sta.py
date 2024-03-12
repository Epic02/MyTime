class Sta:
    """Perform sta"""
    def __init__(self,graph,PI,PO,liberty,prim_node,wires):
        self.graph=graph
        self.PI=PI
        self.PO=PO
        self.liberty=liberty
        self.queue=[]
        self.fan_queue=[]
        self.prim_node=prim_node
        self.critical_path=[]
        self.wires=wires

    def forward_trav(self):
        """Perform topological traversal from all primary nodes"""
        print("in front"+str(len(self.prim_node)))
        for i,inp in enumerate(self.prim_node):
            #print("Node "+str(i)+": "+str(inp.outputs)+" "+str(inp.outname))
            self.queue.append(inp.outname)
            self.topolgcl_trav1()
    def backward_trav(self,delay):
        """Perform backward topological traversal"""
        print("in back")
        for outp in self.PO:
            self.queue.append(outp)
            self.topolgcl_trav2(delay=delay)
    def topolgcl_trav2(self,delay):
        """Perform backward trav"""
        while len(self.queue)>0:
            curr_node=self.graph[self.queue.pop(0)]
            outputs=curr_node.outputs
            RAT=curr_node.RAT
            for outp in outputs:
                if outp == "OUTP":
                    RAT[outp]=1.1*delay
                    #print(RAT)
            if len(outputs) == len(RAT):
                if curr_node.outname in self.wires:
                    curr_node.min_RAT=1.1*delay
                    curr_node.slack=1.1*delay
                else:
                    for i,(brnch,rat) in enumerate(RAT.items()):
                        if i==0:
                            min_rat=rat
                        elif rat<min_rat:
                            min_rat=rat
                    #print(curr_node.outname+"min_rat: "+str(min_rat))
                    curr_node.min_RAT=min_rat
                    curr_node.slack=min_rat-curr_node.max_out_arrival
                    #print(curr_node.outname+"slack: "+str(curr_node.slack))
                    #print(curr_node.outname+"arr_time: "+str(curr_node.max_out_arrival))
                    #print(curr_node.outp_arrival)
                    for i in curr_node.inputs:
                        if not i == "INP" and i not in self.queue:
                            self.queue.append(i)
                        #print(i)
                        self.graph[i].RAT[curr_node.outname]=min_rat-curr_node.outp_arrival[i][1]
            #else:
            #    for i in curr_node.inputs:
            #        if not i == "INP":
            #            self.queue.append(i)


    def topolgcl_trav1(self):
        """Perform topological traversal"""
        while len(self.queue)>0:
            curr_node=self.graph[self.queue.pop(0)]
            inputs=curr_node.inputs
            tau_in=curr_node.Tau_in
            for pin in  inputs:
                if pin in self.PI:
                    tau_in[pin]=0.002
                    curr_node.inp_arrival[pin]=0
                    #print("in prim")
            cload=self.get_cload(curr_node)
            #print("cload = "+str(cload))
            if len(inputs) == len(tau_in):
                
                #print(curr_node.outname)
                for pin in tau_in.keys():
                    delay=self.get_dly_tauout(tau_in[pin],cload,curr_node.name,True,len(curr_node.inputs))
                    curr_node.outp_arrival[pin]=(delay+curr_node.inp_arrival[pin],delay)
                #print(curr_node.outp_arrival)
                tau_max,curr_node.max_out_arrival,curr_node.delay=self.get_max(curr_node.outp_arrival)
                #print(curr_node.max_outp_arrival)
                #tau_max=self.get_max(curr_node.outp_arrival)[0]
                curr_node.Tau_out=self.get_dly_tauout(tau_in[tau_max],cload,curr_node.name,False,len(curr_node.inputs))
                for o in curr_node.outputs:
                    if not o =="OUTP":
                        self.graph[o].Tau_in[curr_node.outname]=curr_node.Tau_out
                        self.graph[o].inp_arrival[curr_node.outname]=curr_node.max_out_arrival
                        if o not in self.queue:
                            self.queue.append(o)
            #else:
            #    for o in curr_node.outputs:
            #        if not o =="OUTP":
            #            self.queue.append(o)

    def get_cload(self,node):
        """Calculates the output load capacitance"""
        cload=0
        #print(node.outputs)
        for o in node.outputs:
            if o=="OUTP":
                cload=cload+(4*float(self.liberty["INV_X1"]["capacitance"]))
            else:
                #print()
                cload=cload+float(self.liberty[self.node_name(self.graph[o].name)]["capacitance"])#*(len(self.graph[o].inputs)/2)
        return cload

    def get_dly_tauout(self,tau,c,gtype, dlytau,n_inputs):
        """Calculates the interpolated delay or tauout for the givenvalues of c and tau """
        inp_slews=self.liberty[self.node_name(gtype)]["inp_slews"]
        load_cap=self.liberty[self.node_name(gtype)]["load_cap"]
        delays=self.liberty[self.node_name(gtype)]["delay" if dlytau else "slew"]
        slw_indx2=0
        cap_indx2=0
        for i,inps in enumerate(inp_slews):
            if tau<float(inps):
                slw_indx2=i
                break
        for i,c_load in enumerate(load_cap):
            if c<float(c_load):
                cap_indx2=i
                break
        multplr=1 if self.node_name(gtype)=="INV_X1" else n_inputs/2
        cap_indx1=cap_indx2-1
        slw_indx1=slw_indx2-1
        C1=float(load_cap[cap_indx1])
        C2=float(load_cap[cap_indx2])
        tau1=float(inp_slews[slw_indx1])
        tau2=float(inp_slews[slw_indx2])
        d11=float(delays[slw_indx1][cap_indx1])*multplr
        d12=float(delays[slw_indx1][cap_indx2])*multplr
        d21=float(delays[slw_indx2][cap_indx1])*multplr
        d22=float(delays[slw_indx2][cap_indx2])*multplr
        d=((d11*(C2-c)*(tau2-tau))+(d12*(c-C1)*(tau2-tau))+(d21*(C2-c)*(tau-tau1))+(d22*(c-C1)*(tau-tau1)))/((C2-C1)*(tau2-tau1))
        return d

    def get_max(self,delays):
        """Returns the max delay and the corresponding pin"""
        key=list(delays.keys())[0]
        max_v=delays[key][0]
        for i in delays.keys():
            if max_v<delays[i][0]:
                max_v=delays[i][0]
                key=i
        return key,max_v,delays[key][1]
    
    def disp_slack(self,ckt_dtls):
        """Prints the slack values pf gates"""
        for pi in self.PI:
            self.prnt_n_write(ckt_dtls,"INPUT-"+self.graph[pi].outname+": "+str(round(1000*self.graph[pi].slack,4))+" ps")
        for po in self.PO:
            self.prnt_n_write(ckt_dtls,"OUTPUT-"+self.graph[po].outname+": "+str(round(1000*self.graph[po].slack,4))+" ps")
        for node in self.prim_node:             #   Iterate through the primary input nodes 
            self.fan_queue.append(node)          #   Add the primary input node to the queue
            self.scan_slack(ckt_dtls) 
    
    def scan_slack(self,ckt_dtls):
        """Scans the graph for fanouts or fanins"""
        while len(self.fan_queue)>0:             #   Run through the queue until its empty
            node=self.fan_queue.pop(0)       #   Get the first element of queue
            n=len(node.outputs)             
            for op in range(n):           #   Iterate through all the nodes in the outputs list of the node
                if not node.outputs[op] == "OUTP":      #   If the node is not primary output node
                    
                    if not self.graph[node.outputs[op]] in self.fan_queue and self.graph[node.outputs[op]].disp_slack == 0:
                        self.fan_queue.append(self.graph[node.outputs[op]])
                    elif node.outputs[op] in self.PO:
                        self.fan_queue.append(self.graph[node.outputs[op]])
                    
                    self.graph[node.outputs[op]].disp_slack=self.graph[node.outputs[op]].disp_slack+1
                    if op==n-1:
                        self.prnt_n_write(ckt_dtls,node.name+"-"+node.outname+": "+str(round(1000*node.slack,4))+" ps")
                elif node.disp_slack >= node.inp_count and not node.disp_slack_vst:
                    node.disp_slack_vst = True
                    self.prnt_n_write(ckt_dtls,node.name+"-"+node.outname+": "+str(round(1000*node.slack,4))+" ps")

    def get_critical_pth(self):
        """Returns the critical path"""
        self.get_min_slck_node(self.PO)
        return self.critical_path

    def get_min_slck_node(self,arr):
        """Backward traverses along the min slack path""" 
        for i,po in enumerate(arr):
            if i==0:
                min_slack = self.graph[po].slack
                node=po
            elif self.graph[po].slack<min_slack:
                min_slack = self.graph[po].slack
                node=po
        self.critical_path.append(node)
        if not self.graph[node].name=="INP":
            self.get_min_slck_node(self.graph[node].inputs)

    def get_ckt_dly(self):
        """Get delay of the cicuit"""
        ckt_delay=self.graph[self.PO[0]].max_out_arrival
        for po in self.PO:
            if ckt_delay < self.graph[po].max_out_arrival:
                ckt_delay=self.graph[po].max_out_arrival
        return ckt_delay

    def get_ckt_dly_ps(self):
        """Get delay of circuit in ps"""
        return round(self.get_ckt_dly()*1000,4)

    def prnt_n_write(self,file, txt):
        """Print and write to given file"""
        print(txt)
        file.write(txt+"\n")

    def node_name(self,name):
        """Provides exact gate names for the liberty file"""
        if name == "INV" or name == "NOT":
            return "INV_X1"
        elif name in ["NAND","XOR","OR","AND","NOR"]:
            return name+"2_X1"
        elif name == "BUFF" or name == "BUF":
            return "BUF_X1"
        else:
            return name+"_X1"
            #return (name+"2" if name in ["NAND","XOR","OR","AND","NOR"] else name)+"_X1"
