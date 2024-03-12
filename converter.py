import re

from node import Node

class Converter:
    """Converts given netlist to a graph"""
    def __init__(self,print):
        self.PI=[]               # Keeps track of all the primary inputs
        self.PO=[]               # Keeps track of all the primary inputs
        self.gate_count={}       # Tracks the count of each type of gate
        self.nodes={}            # Holds all the nodes/gates in the circuit
        self.primary_nodes=[]    # Holds the primary node - nodes which have all primary inputs
        self.fan_queue=[]        # Keeps track of each gate/node that needs to processed while traversing the graph
        self.wires=[]
        self.print=print
        self.lib_file ={}


    def read_circuit(self,path):

        PI_count=0      # Counts number of primary inputs
        PO_count=0      # Counts number of primary inputs
        
        with path.open(mode="r",encoding="utf-8") as circuit, open("ckt_details.txt", mode="w", encoding="utf-8") as ckt_dtls:

            ckt=circuit.read()                                  #   Reads in the file

            for line in ckt.splitlines():                       #   Loop through each line of the file
                if not re.search("^#",line):                    #   Process only which do not start with hash-tag
                    if re.search("^INPUT",line):                #   Check if line starts with INPUT
                        inp_name=line[line.find("(")+1:line.find(")")]
                        self.nodes[inp_name]=Node(name="INP",outname=inp_name)
                        self.PI.append(inp_name)    #   Load the names of the primary input which lie between brackets into PI
                        PI_count=PI_count+1                                 #   Count primary inputs
                    elif re.search("^OUTPUT",line):             #   Check if line starts with OUTPUT
                        outp_name=line[line.find("(")+1:line.find(")")]
                        self.nodes[outp_name]=Node(name="OUTP",outname=outp_name)
                        self.PO.append(outp_name)    #   Load the names of the primary outputs which lie between brackets into PO
                        PO_count=PO_count+1                     #   Count primary outputs
                    else:
                        if(len(line.strip())):                  #   Check if line is not empty
                            self.ckt_to_graph(line=line)            #   Convert circuit to graph

            self.wires = list(set(self.PI).intersection(self.PO))         #   Finds any wires in the circuit by finding intersection between PI and PO

            #print(wires)
            self.prnt_n_write(ckt_dtls,"------------------------------------------")
            self.prnt_n_write(ckt_dtls,str(PI_count)+" primary inputs")
            self.prnt_n_write(ckt_dtls,str(PO_count)+" primary outputs")
            self.disp_gc(self.gate_count,ckt_dtls)
            self.prnt_n_write(ckt_dtls,"\nFanout...")
            self.disp_fanout(self.primary_nodes,ckt_dtls)
            self.prnt_n_write(ckt_dtls,"\nFanin...")
            self.disp_fanin(self.primary_nodes,ckt_dtls)
            self.prnt_n_write(ckt_dtls,"------------------------------------------")
            ckt_dtls.close()


    def ckt_to_graph(self,line):
        isPrimary=True
        strp_line=line.strip()          #   Remove starting and trailing whitespaces in line if any
        equal_to=line.find("=")         #   Get index location of "="
        opn_brckt=line.find("(")        #   Get index location of "("
        clo_brckt=line.find(")")        #   Get index location of ")"

        node=Node()                     #   Instansiate a node
        
        node.name=strp_line[equal_to+1:opn_brckt].strip()       #   Get type of node from whatever lies between "=" and "(" and strip whitespaces
        if node.name not in self.gate_count:                         #   Check if the gate is present in gate count tracker
            self.gate_count[node.name]=1                             #   If gate not already present create entry with value 1
        else:
            self.gate_count[node.name]=self.gate_count[node.name]+1       #   If gate present increment the value with 1
        node.outname=strp_line[:equal_to].strip()               #   Get the outname from LHS of "="
        inputs=strp_line[opn_brckt+1:clo_brckt].split(",")      #   Get the comma seperated inputs between "(" and ")" and split them using ","
        count = 0
        for ckt_input in inputs:            #   Iterate through all the inputs
            strp_i=ckt_input.strip()        #   Remove whitespaces if any in the start and end
            node.inputs.append(strp_i)          #   Add the input to the inputs list of the node
            if strp_i not in self.PI:
                count = count + 1
                isPrimary=False         #   If any of the input is not primary input the node/gate will not marked as primary
            if strp_i in self.nodes:
                self.nodes[strp_i].outputs.append(node.outname)      #   If the input of the current node is output of someothere node add this node
                                                                    #   to the ouputs list of the node which is the input for this node
        node.inp_count = count
        if node.outname in self.PO:
            #self.prnt_n_write("PARSER "+node.outname)
            node.outputs.append("OUTP")         #   Add OUTP to the outputs list if its a primary output node
        if isPrimary:
            self.primary_nodes.append(node)          #   If node has all primary inputs and it to list of primary inputs
        
        self.nodes[node.outname]=node        #   Add the processed node to the dictionary holding all the node instances
        

    def disp_fanout(self,prim_nodes,ckt_dtls):
        for node in prim_nodes:             #   Iterate through the primary input nodes 
            self.fan_queue.append(node)          #   Add the primary input node to the queue
            self.scan_fan(1,ckt_dtls)                     #   Traverse the graph/circuit
        self.disp_wires(1,ckt_dtls)
        return

    def scan_fan(self,fan_io,ckt_dtls):
        """Scans the graph for fanouts or fanins"""
        while len(self.fan_queue)>0:             #   Run through the queue until its empty
            node=self.fan_queue.pop(0)           #   Get the first element of queue
            fan=node.name+"-n"+node.outname+": "        #   Create string stating gate type and node name
            n=len(node.outputs)             
            for op in range(n-1):           #   Iterate through all the nodes in the outputs list of the node
                if not node.outputs[op] == "OUTP":      #   If the node is not primary output node
                    
                    if not self.nodes[node.outputs[op]] in self.fan_queue and self.nodes[node.outputs[op]].visit_count == 0:
                        self.fan_queue.append(self.nodes[node.outputs[op]])
                    elif node.outputs[op] in self.PO:
                        self.fan_queue.append(self.nodes[node.outputs[op]])
                    
                    self.nodes[node.outputs[op]].visit_count=self.nodes[node.outputs[op]].visit_count+1
                    fan=fan+ (self.outputs_str(node,op,n-1) if fan_io else "")
                else:
                    fan=fan+"OUTP"
            print(node.outname+" "+str(node.outputs))
            if not node.outputs[n-1] == "OUTP":
                if not self.nodes[node.outputs[n-1]] in self.fan_queue and self.nodes[node.outputs[n-1]].visit_count == 0:
                    self.fan_queue.append(self.nodes[node.outputs[n-1]])
                elif node.outputs[n-1] in self.PO:
                    self.fan_queue.append(self.nodes[node.outputs[n-1]])
                self.nodes[node.outputs[n-1]].visit_count=self.nodes[node.outputs[n-1]].visit_count+1
                fan=fan+(self.outputs_str(node,n-1,n-1) if fan_io else self.inputs_str(node))
                self.prnt_n_write(ckt_dtls,fan)
            elif node.visit_count >= (node.inp_count) and not node.all_inp_vstd:
                node.all_inp_vstd = True
                fan=fan+("OUTP" if fan_io else self.inputs_str(node))
                self.prnt_n_write(ckt_dtls,fan)

    def disp_fanin(self,prim_nodes,ckt_dtls):
        """Displays the fanin of each gate"""
        for key,value in self.nodes.items():
            value.visit_count=0
            value.all_inp_vstd=False
        for node in prim_nodes:
            self.fan_queue.append(node)
            self.scan_fan(0,ckt_dtls)
        self.disp_wires(0,ckt_dtls)

    def inputs_str(self,node):
        istr=""
        n=len(node.inputs)
        for i in range(n):
            if node.inputs[i] in self.PI:
                istr=istr+"INP-n"+node.inputs[i]+(" " if i==n-1 else ", ")
            else:
                istr=istr+node.name+"-n"+node.inputs[i]+(" " if i==n-1 else ", ")
        return istr

    def outputs_str(self,node,i,size):
        return self.nodes[node.outputs[i]].name+"-n"+self.nodes[node.outputs[i]].outname+("" if i==size else ", ")

    def disp_wires(self,fio,ckt_dtls):
        for w in self.wires:
            self.prnt_n_write(ckt_dtls,("INP" if fio else "OUTP") + "-n" + w + ": " + ("OUTP" if fio else "INP") + "-n" + w)

    def disp_gc(self,gc,ckt_dtls):
        for gate in gc:
            self.prnt_n_write(ckt_dtls,str(gc[gate])+" "+gate+" gates")

    def prnt_n_write(self,file, txt):
        if self.print:
            print(txt)
            file.write(txt+"\n")
        
    def read_nldm(self,path, d_or_s):
        lut_type = ("delay" if d_or_s else "slew")
        inCell=False
        inLut=False
        inVal=False
        curl_count=False
        toFile=""
        cell=""
        
        with path.open(mode="r",encoding="utf-8") as lib, open((lut_type + "_LUT.txt"), mode="w", encoding="utf-8") as lut:
            self.prnt_n_write(lut,"------------------------------------------")
            lib_lines = lib.read()
            for line in lib_lines.splitlines():
                #print(line)
                clo_curly = ("}" in line)
                clo_brkt = (")" in line)
                line=line.strip()
                if re.search("^cell",line) or inCell:
                    if re.search("{",line):
                        if not inCell:
                            inCell=True
                            cell=str(line[line.find("(")+1:line.find(")")])
                            if cell not in self.lib_file:
                                #print("JKNKJN")
                                self.lib_file[cell]={}
                            toFile="cell: "+line[line.find("(")+1:line.find(")")]
                            self.prnt_n_write(lut,toFile)
                        elif re.search(lut_type,line):
                            #print("Insl")
                            inLut=True
                    elif re.search("^capacitance",line):
                        self.lib_file[cell]["capacitance"]=line[line.find(":")+1:line.find(";")].strip()
                        #print("CAP")
                        #print(line[line.find(":")+1:line.find(";")].strip())
                    elif inLut:
                        if re.search("^index_1",line):
                            
                            #self.lib_file[cell]["inp_slews"]=line[line.find("(")+2:line.find(")")-1].split(",")
                            self.lib_file[cell]["inp_slews"]=line[line.find("(")+2:line.find(")")-1].split(",")
                            self.lib_file[cell][lut_type]=[]
                            toFile="input slews: " + line[line.find("(")+2:line.find(")")-1]
                            self.prnt_n_write(lut,toFile)
                        elif re.search("^index_2", line):
                            self.lib_file[cell]["load_cap"]=line[line.find("(")+2:line.find(")")-1].split(",")
                            toFile="load cap: " + line[line.find("(")+2:line.find(")")-1].strip()
                            self.prnt_n_write(lut,toFile)
                        elif re.search("^values",line):
                            toFile="\n"+lut_type+"s: "
                            self.prnt_n_write(lut,toFile)
                            if clo_brkt:
                                toFile=re.findall(r'"(.*?)"', line)[0]
                                self.lib_file[cell][lut_type].append(toFile.split(","))
                                self.prnt_n_write(lut,toFile)
                            elif len(line[line.find("(")+1:])>0:
                                toFile=re.findall(r'"(.*?)"', line)[0]
                                self.lib_file[cell][lut_type].append(toFile.split(","))
                                self.prnt_n_write(lut,toFile)
                                inVal=True
                            else:
                                inVal=True
                        elif clo_brkt and inVal:
                            toFile=re.findall(r'"(.*?)"', line)[0]
                            self.lib_file[cell][lut_type].append(toFile.split(","))
                            self.prnt_n_write(lut,toFile+"\n")
                            inVal=False
                        elif inVal:
                            toFile=re.findall(r'"(.*?)"', line)[0]
                            self.lib_file[cell][lut_type].append(toFile.split(","))
                            self.prnt_n_write(lut,toFile)
                        elif clo_curly:
                            inLut=False
                            curl_count=True
                    elif clo_curly and curl_count:
                        inCell=False
                        curl_count=False
            to_file="------------------------------------------"
            self.prnt_n_write(lut,to_file)
            #print(self.lib_file)