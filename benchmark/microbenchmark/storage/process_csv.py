import sys

def process_read_lat_thru(result_row, block_count, batch_size):
	result_row = result_row[-2:]
	result_row[0] = result_row[0].replace('s', '').strip()

	thru = result_row[1].strip().split(' ')
	if thru[-1] == "GB/s":
		thru[0] = float(thru[0].strip())
	if thru[-1] == "MB/s":
		thru[0] = float(thru[0].strip())/1000
	if thru[-1] == "KB/s":
		thru[0] = float(thru[0].strip())/(1000*1000)

	result_row = "{}, {}, {}\n".format(batch_size, result_row[0], thru[0])

	return result_row

def process_write_lat(result_row, count, batch_size):
	result_row = result_row[-2:]
	result_row[0] = result_row[0].replace('s', '').strip()

	result_row = "{}, {}\n".format(batch_size, result_row[0])

	return result_row

def process_write_thru(result_row, batch_size):
	result_row = result_row[-2:]

	thru = result_row[1].strip().split(' ')
	if thru[-1] == "GB/s":
		thru[0] = float(thru[0].strip())
	if thru[-1] == "MB/s":
		thru[0] = float(thru[0].strip())/1000
	if thru[-1] == "KB/s":
		thru[0] = float(thru[0].strip())/(1000*1000)

	result_row = "{}, {}\n".format(batch_size, thru[0])

	return result_row


def main():
	test_kind  = sys.argv[1] #r or w
	test_type  = sys.argv[2] #l or t or b
	res        = sys.argv[3]
	count      = sys.argv[4]
	batch_size = sys.argv[5]
	out_file   = sys.argv[6]
	res = res.split(',')
	print(res)

	if test_kind == 'r':
		res = process_read_lat_thru(res, count, batch_size)
	if test_kind == 'w':
		if test_type == 'l':
			res = process_write_lat(res, count, batch_size)
		if test_type == 't':
			res = process_write_thru(res, batch_size)
	
	with open(out_file, 'a') as f:
		f.write(res)

if __name__=='__main__':
	main()