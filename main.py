from argparse import ArgumentParser
from pathlib import Path

from converter import Converter
from sta import Sta

parser = ArgumentParser()
parser.add_argument("--read_ckt")
parser.add_argument("--read_nldm")
args=parser.parse_args()
path=Path(args.read_ckt)
lib_path=Path(args.read_nldm)

conv=Converter(print=True)

if args.read_ckt and args.read_nldm:
    conv.read_circuit(path)
    conv.read_nldm(lib_path, True)
    conv.read_nldm(lib_path, False)
    sta_engine=Sta(graph=conv.nodes,
                   PI=conv.PI,
                   PO=conv.PO,
                   wires=conv.wires,
                   liberty=conv.lib_file,
                   prim_node=conv.primary_nodes,
                   ff=conv.ff_node)
    with open("ckt_traversal.txt", mode="w", encoding="utf-8") as ckt_trav:
        sta_engine.forward_trav()
        #print("delay: "+str(sta_engine.get_ckt_dly()))
        sta_engine.backward_trav(sta_engine.get_ckt_dly())
        sta_engine.prnt_n_write(file=ckt_trav,txt="-------------------------")
        sta_engine.prnt_n_write(file=ckt_trav,txt="Circuit delay: "+str(sta_engine.get_ckt_dly_ps())+"ps\n")
        sta_engine.disp_slack(ckt_dtls=ckt_trav)
        crtcl_pth_str=""
        crtcl_path=sta_engine.get_critical_pth()
        crtcl_path.reverse()
        for n in crtcl_path:
            if not (n in conv.PI or n in conv.PO):
                crtcl_pth_str=crtcl_pth_str+sta_engine.graph[n].name+"-"+n+", "
            else:
                if n in conv.PI:
                    crtcl_pth_str=crtcl_pth_str+"INPUT-"+n+", "
                if n in conv.PO:
                    crtcl_pth_str=crtcl_pth_str+sta_engine.graph[n].name+"-"+n+", OUTPUT-"+n
                    #crtcl_pth_str=crtcl_pth_str+"OUTPUT-"+n+", "
        sta_engine.prnt_n_write(file=ckt_trav,txt="\nCrtical Path:")
        sta_engine.prnt_n_write(file=ckt_trav,txt=crtcl_pth_str)

else:
    parser.print_help()
