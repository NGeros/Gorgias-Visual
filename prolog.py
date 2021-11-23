from argparse import ArgumentParser
from pyswip import Prolog
from sys import stderr

# Defaults
resultVariable = "A"
queryFunction = "extended_prove_with_tree"

# Create interaction object 
prolog = Prolog()

def main():

    parser = ArgumentParser()
    parser.add_argument("-f", "--filename", required=True)

    parser.add_argument("-q", "--query", required=True)
    parser.add_argument("-r", "--resultVariable", required=False, default=resultVariable)
    parser.add_argument("-x", "--queryFunction", required=False, default=queryFunction)
    args = parser.parse_args()
    
    #Build query
    query = args.queryFunction+"(["+args.query+"],"+args.resultVariable+")"

    #Consult pl file
    prolog.consult(args.filename.replace("\\","/"))

    #Run it and get all results
    try:
        for next in prolog.query(query):
            pass #Simply running the query sends the output to stdout. No need to print

    except Exception as e:
        print(e,file=stderr)
        pass


if __name__ == "__main__":
	main()        