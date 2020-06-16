import sys
import pandas as pd

def compare_csv(trad, ndp):
	trad = pd.read_csv(trad, sep='|')
	ndp  = pd.read_csv(ndp, sep='|')

	c = pd.concat([trad,ndp], axis=0)
	c.drop_duplicates(keep=False, inplace=True)

	c.reset_index(drop=True, inplace=True)
	print(len(c.index))

if __name__ == "__main__":
	compare_csv(sys.argv[1], sys.argv[2])