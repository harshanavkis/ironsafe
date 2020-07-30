import sys
import pandas as pd

def process_chunk(chunks):
	for i in range(len(chunks)):
		chunks[i][0] = i+1

	chunks = [i for i in chunks if "Tested" in i[1]]

	chunks = [[i[0], i[2], i[4], i[6]] for i in chunks]

	return chunks

def process_sql(sql_file, out_file):
	with open(sql_file) as f:
		content = f.readlines()

	content = [x.strip() for x in content]
	content = [x for x in content if len(x) > 0]

	num_entries = len(content)/22

	if int(num_entries) != num_entries:
		print("sql file format is not correct")
		return

	chunks = [content[x:x+8] for x in range(0, len(content), 8)]

	chunks = process_chunk(chunks)

	chunks = pd.DataFrame(chunks)

	chunks.to_csv(out_file, index=False, header=False, sep='|')

if __name__ == "__main__":
	sql_file = sys.argv[1]
	out_file = sys.argv[2]

	process_sql(sql_file, out_file)