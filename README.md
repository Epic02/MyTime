

**requirements.txt** => contains the list of packages required to run the python code

**sta_parser.py** => Contains the python required to parse the given benchmark file

**node.py** => Describe the class representation for each node

**Commands:**

**pip3 install -r requirements.txt**

**python3.7 sta_parser.py --read_ckt <benchmark_file>**

(Parses the benchmark file to create a graph representation of the circuit)

**python3.7 sta_parser.py --delays --read_nldm <liberty_file>** 

(Parses the given liberty file and outputs, delays and the corresponding capacitances and input slews of the gates)

**python3.7 sta_parser.py --slews --read_nldm <liberty_file>** 

(Parses the given liberty file and outputs, output slews and the corresponding capacitances and input slews of the gates)

**python3.7 main.py --read_ckt <benchmark_file> --read_nldm <liberty_file>**

(Parses the benchmark file and outputs the slacks and critical path of the given combinational logic)
