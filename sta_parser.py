#from pyinstrument import Profiler   #to analyse perfomance
from argparse import ArgumentParser
from pathlib import Path
import re

from converter import Converter
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

converter = Converter(print=True)
if args.read_ckt:
    converter.read_circuit(path)
elif args.delays and args.read_nldm:
    converter.read_nldm(path, True)
elif args.slews and args.read_nldm:
    converter.read_nldm(path, False)
else:
    parser.print_help()

#profiler.stop()
#profiler.open_in_browser()         #Analyse program code perfomance
    