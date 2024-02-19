#from pyinstrument import Profiler   #to analyse perfomance
from argparse import ArgumentParser
from pathlib import Path
from node import Node
import re

#profiler=Profiler()
#profiler.start()

parser=ArgumentParser()

parser.add_argument("file")
parser.add_argument("--read_ckt",action="store_true")
parser.add_argument("--delays",action="store_true")
parser.add_argument("--slews",action="store_true")
parser.add_argument("--read_nldm",action="store_true")
args=parser.parse_args()

path=Path(args.file)

if not path.exists():
    print("File does not exist")
    raise SystemExit(1)
elif not bool(re.search(".bench$|.lib$",path.name)):
    print("Wrong file type")
    raise SystemExit(1)


PI=[]               # Keeps track of all the primary inputs
PO=[]               # Keeps track of all the primary inputs
gate_count={}       # Tracks the count of each type of gate
nodes={}            # Holds all the nodes/gates in the circuit
primary_nodes=[]    # Holds the primary node - nodes which have all primary inputs
fan_queue=[]        # Keeps track of each gate/node that needs to processed while traversing the graph
wires=[]
ckt_dtls =  open("ckt_details.txt", "w")


def read_circuit(path):

    PI_count=0      # Counts number of primary inputs
    PO_count=0      # Counts number of primary inputs
    
    with path.open(mode="r",encoding="utf-8") as circuit:

        ckt=circuit.read()                                  #   Reads in the file

        for line in ckt.splitlines():                       #   Loop through each line of the file
            if not re.search("^#",line):                    #   Process only which do not start with hash-tag
                if re.search("^INPUT",line):                #   Check if line starts with INPUT
                    PI.append(line[line.find("(")+1:line.find(")")])    #   Load the names of the primary input which lie between brackets into PI
                    PI_count=PI_count+1                                 #   Count primary inputs
                elif re.search("^OUTPUT",line):             #   Check if line starts with OUTPUT
                    PO.append(line[line.find("(")+1:line.find(")")])    #   Load the names of the primary outputs which lie between brackets into PO
                    PO_count=PO_count+1                     #   Count primary outputs
                else:
                    if(len(line.strip())):                  #   Check if line is not empty
                        ckt_to_graph(line=line)             #   Convert circuit to graph

        global wires 
        wires = [wi for wi in set(PI).intersection(PO)]         #   Finds any wires in the circuit by finding intersection between PI and PO

        #print(wires)
        prnt_n_write(ckt_dtls,"------------------------------------------")
        prnt_n_write(ckt_dtls,str(PI_count)+" primary inputs")
        prnt_n_write(ckt_dtls,str(PO_count)+" primary outputs")
        disp_gc(gate_count)
        prnt_n_write(ckt_dtls,"\nFanout...")
        disp_fanout(primary_nodes)
        prnt_n_write(ckt_dtls,"\nFanin...")
        disp_fanin(primary_nodes)
        prnt_n_write(ckt_dtls,"------------------------------------------")
        ckt_dtls.close()


def ckt_to_graph(line):
    isPrimary=True
    strp_line=line.strip()          #   Remove starting and trailing whitespaces in line if any
    equal_to=line.find("=")         #   Get index location of "="
    opn_brckt=line.find("(")        #   Get index location of "("
    clo_brckt=line.find(")")        #   Get index location of ")"

    node=Node()                     #   Instansiate a node

    node.name=strp_line[equal_to+1:opn_brckt].strip()       #   Get type of node from whatever lies between "=" and "(" and strip whitespaces
    if not node.name in gate_count:                         #   Check if the gate is present in gate count tracker
        gate_count[node.name]=1                             #   If gate not already present create entry with value 1
    else:
        gate_count[node.name]=gate_count[node.name]+1       #   If gate present increment the value with 1
    node.outname=strp_line[:equal_to].strip()               #   Get the outname from LHS of "="
    inputs=strp_line[opn_brckt+1:clo_brckt].split(",")      #   Get the comma seperated inputs between "(" and ")" and split them using ","
    count = 0
    for input in inputs:            #   Iterate through all the inputs
        strp_i=input.strip()        #   Remove whitespaces if any in the start and end
        node.inputs.append(strp_i)          #   Add the input to the inputs list of the node
        if strp_i not in PI: 
            count = count + 1
            isPrimary=False         #   If any of the input is not primary input the node/gate will not marked as primary
            if strp_i in nodes:
                nodes[strp_i].outputs.append(node.outname)      #   If the input of the current node is output of someothere node add this node
                                                                #   to the ouputs list of the node which is the input for this node
    node.inp_count = count
    if node.outname in PO:
        node.outputs.append("OUTP")         #   Add OUTP to the outputs list if its a primary output node
    if isPrimary:
        primary_nodes.append(node)          #   If node has all primary inputs and it to list of primary inputs
    
    nodes[node.outname]=node        #   Add the processed node to the dictionary holding all the node instances
    

def disp_fanout(prim_nodes):
    for node in prim_nodes:             #   Iterate through the primary input nodes 
        fan_queue.append(node)          #   Add the primary input node to the queue
        scan_fan(1)                     #   Traverse the graph/circuit
    disp_wires(1)
    return

def scan_fan(fan_io):
    while len(fan_queue)>0:             #   Run through the queue until its empty
        node=fan_queue.pop(0)           #   Get the first element of queue
        fan=node.name+"-n"+node.outname+": "        #   Create string stating gate type and node name
        n=len(node.outputs)             
        for op in range(n-1):           #   Iterate through all the nodes in the outputs list of the node
            if not node.outputs[op] == "OUTP":      #   If the node is not primary output node
                
                if not nodes[node.outputs[op]] in fan_queue and nodes[node.outputs[op]].visit_count == 0:
                    fan_queue.append(nodes[node.outputs[op]])
                elif node.outputs[op] in PO:
                    fan_queue.append(nodes[node.outputs[op]])
                
                nodes[node.outputs[op]].visit_count=nodes[node.outputs[op]].visit_count+1
                fan=fan+ (outputs_str(node,op,n-1) if fan_io else "")
            else:
                fan=fan+"OUTP"
        
        if not node.outputs[n-1] == "OUTP":
            
            if not nodes[node.outputs[n-1]] in fan_queue and nodes[node.outputs[n-1]].visit_count == 0:
                fan_queue.append(nodes[node.outputs[n-1]])
            elif node.outputs[n-1] in PO:
                    fan_queue.append(nodes[node.outputs[n-1]])
            nodes[node.outputs[n-1]].visit_count=nodes[node.outputs[n-1]].visit_count+1
            fan=fan+(outputs_str(node,n-1,n-1) if fan_io else inputs_str(node))
            prnt_n_write(ckt_dtls,fan)
        elif node.visit_count >= (node.inp_count) and not node.all_inp_vstd:
            node.all_inp_vstd = True
            fan=fan+("OUTP" if fan_io else inputs_str(node))
            prnt_n_write(ckt_dtls,fan)
       

def disp_fanin(prim_nodes):
    
    for key in nodes:
        nodes[key].visit_count=0
        nodes[key].all_inp_vstd=False
    for node in prim_nodes:
        fan_queue.append(node)
        scan_fan(0)
    disp_wires(0)
    return
    
def inputs_str(node):
    istr=""
    n=len(node.inputs)
    for i in range(n):
        if node.inputs[i] in PI:
            istr=istr+"INP-n"+node.inputs[i]+(" " if i==n-1 else ", ")
        else:
            istr=istr+node.name+"-n"+node.inputs[i]+(" " if i==n-1 else ", ")
    return istr

def outputs_str(node,i,size):
    return nodes[node.outputs[i]].name+"-n"+nodes[node.outputs[i]].outname+("" if i==size else ", ")

def disp_wires(fio):
        for w in wires:
            prnt_n_write(ckt_dtls,("INP" if fio else "OUTP") + "-n" + w + ": " + ("OUTP" if fio else "INP") + "-n" + w)

def disp_gc(gc):
    for gate in gc:
        prnt_n_write(ckt_dtls,str(gc[gate])+" "+gate+" gates")

def prnt_n_write(file, txt):
    print(txt)
    file.write(txt+"\n")
    
def read_nldm(path, d_or_s):
    lut_type = ("delay" if d_or_s else "slew")
    inCell=False
    inLut=False
    inVal=False
    curl_count=False
    toFile=""
    with path.open(mode="r",encoding="utf-8") as lib, open((lut_type + "_LUT.txt"), "w") as lut:
        prnt_n_write(lut,"------------------------------------------")
        lib_lines = lib.read()
        for line in lib_lines.splitlines():
            #print(line)
            opn_curly = ("{" in line)
            clo_curly = ("}" in line)
            opn_brkt = ("(" in line)
            clo_brkt = (")" in line)
            line=line.strip()
            if re.search("^cell",line) or inCell:
                if re.search("{",line):
                    if not inCell:
                        inCell=True
                        toFile="cell: "+line[line.find("(")+1:line.find(")")]
                        prnt_n_write(lut,toFile)
                    elif re.search(lut_type,line):
                        #print("Insl")
                        inLut=True
                elif inLut:
                    if re.search("^index_1",line):
                        toFile="input slews: " + line[line.find("(")+2:line.find(")")-1]
                        prnt_n_write(lut,toFile)
                    elif re.search("^index_2", line):
                        toFile="load cap: " + line[line.find("(")+2:line.find(")")-1].strip()
                        prnt_n_write(lut,toFile)
                    elif re.search("^values",line):
                        toFile="\n"+lut_type+"s: "
                        prnt_n_write(lut,toFile)
                        if clo_brkt:
                            toFile=re.findall(r'"(.*?)"', line)[0]
                            prnt_n_write(lut,toFile)
                        elif len(line[line.find("(")+1:])>0:
                            toFile=re.findall(r'"(.*?)"', line)[0]
                            prnt_n_write(lut,toFile)
                            inVal=True
                        else:
                            inVal=True
                    elif clo_brkt and inVal:
                        toFile=re.findall(r'"(.*?)"', line)[0]+"\n"
                        prnt_n_write(lut,toFile)
                        inVal=False
                    elif inVal:
                        toFile=re.findall(r'"(.*?)"', line)[0]
                        prnt_n_write(lut,toFile)
                    elif clo_curly:
                        inLut=False
                        curl_count=True
                elif clo_curly and curl_count:
                    inCell=False
                    curl_count=False
        toFile="------------------------------------------"
        prnt_n_write(lut,toFile)
                



if args.read_ckt:
    read_circuit(path)
elif args.delays and args.read_nldm:
    read_nldm(path, True)
elif args.slews and args.read_nldm:
    read_nldm(path, False)
else:
    parser.print_help()

#profiler.stop()
#profiler.open_in_browser()         #Analyse program code perfomance