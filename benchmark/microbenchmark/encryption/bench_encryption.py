import sys
import subprocess
import os
from pathlib import Path
from shutil import copyfile

SRC_DIR = os.path.realpath("../../../")
CURR_DIR = os.path.realpath(".")
TPCH_DATA_DIR = os.path.join(SRC_DIR, "tpch/build/")

DB_FILE_NAME   = "TPCH-{}.db"
FRESH_DB_NAME  = "TPCH-{}-fresh-enc.db"
MERK_FILE_NAME = "merkle-tree-{}.bin"
ENC_IMAGE_NAME = "TPCH-DM-CRYPT-{}.img"
KEYFILE        = "DM-CRYPT-KEY-{}.keyfile"

"""
	Environment variables:
		- SCALE_FACTOR
"""

def run_local_proc(cmd):
	proc = subprocess.run(cmd, stdout=stdout)
	return proc

def setup_stuff():
	try:
		scale_factor = float(os.environ["SCALE_FACTOR"])
	except Exception as e:
		print("SCALE_FACTOR should be a number, preferably a float")
		sys.exit(1)

	db_file = Path(os.path.join(TPCH_DATA_DIR, DB_FILE_NAME.format(scale_factor)))
	if not db_file.is_file():
		os.chdir(f"{SRC_DIR}/tpch")
		cmd = ["./create_db.sh", f"{scale_factor}"]
		proc = run_local_proc(cmd)
		proc.wait()

	img_file = Path(os.path.join(TPCH_DATA_DIR, TPCH-DM-CRYPT.format(scale_factor)))
	if not img_file.is_file():
		img_size = scale_factor*1.2*1.5
		subprocess.run(
				[
					"dd",
					"if=/dev/zero",
					f"of={img_file}",
					"bs=1M",
					"count=0",
					f"seek={img_size}"
				]
			)

		subprocess.run(
				[
					"dd",
					"if=/dev/urandom",
					f"of={os.path.join(TPCH_DATA_DIR, KEYFILE.format(scale_factor))}",
					"bs=1024",
					"count=1"
				]
			)

		subprocess.run(
				[
					"sudo",
					"cryptsetup",
					"luksFormat",
					f"{img_file}",
					f"{KEYFILE.format(scale_factor)}"
				],
				input="YES"
			)

		subprocess.run(
				[
					"sudo",
					"cryptsetup",
					"luksOpen",
					f"{img_file}",
					"benchEncryptVol",
					"--key-file",
					f"{KEYFILE.format(scale_factor)}"
				]
			)

		subprocess.run(["sudo", "mkfs.ext4", "/dev/mapper/benchEncryptVol"])
		subprocess.run(["sudo", "mount", "/dev/mapper/benchEncryptVol", "/mnt"])
		subprocess.run(["sudo", "chown", "-R", "$USER", "/mnt"])

		copyfile(db_file, os.path.join("/mnt", DB_FILE_NAME.format(scale_factor)))

		subprocess.run(["sudo", "umount", "/mnt"])
		subprocess.run(["sudo", "cryptsetup", "luksClose", "benchEncryptVol"])

	os.chdir(CURR_DIR)

def main():
	pass

if __name__=="__main__":
	main()