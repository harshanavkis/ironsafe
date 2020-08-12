import sqlite3
import pandas as pd
import numpy as np

def determine_split(db, split, col):
	conn = sqlite3.connect(db)
	df   = pd.read_sql_query("SELECT * from lineitem", conn)

	extract_date = pd.to_datetime(df[col])
	extract_date = extract_date.values
	extract_date.sort()
	unique_dates = np.unique(extract_date)

	less_than_distr = []
	for i in unique_dates:
		n = len(np.where(extract_date <= np.datetime64(i))[0])/len(extract_date)
		less_than_distr.append(n)

	index = 0
	for i in range(len(less_than_distr)):
		if less_than_distr[i] >= split:
			index = i
			break

	split_date = str(unique_dates[index]).split('T')

	return split_date[0]

# if __name__=="__main__":
# 	main()