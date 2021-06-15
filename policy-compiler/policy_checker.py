import sys
import json
import os
import csv

policy_predicates = [
    "sessionKeyIs",
    "storageLocIs",
    "fwVersion",
    "hostQuery",
    "storageQuery",
    "query"
]

fw_ver_attributes = [
    "host",
    "storage",
]

def check_policy(user_policy_dict):
    '''
        Check that the user submitted policy has the
        correct attributes.
    '''
    for i in user_policy_dict:
        if i not in policy_predicates:
            print(f"We do not support policy predicate: {i}")
            sys.exit(1)
        if i == "fwVersion":
            for j in user_policy_dict[i]:
                if j not in fw_ver_attributes:
                    print(f"We do not support \"{j}\" for firmware version attributes")
                    sys.exit(1)

def check_node_location(user_locs, node_loc):
    '''
        - user_locs is a list of region codes in lowercase
    '''
    user_locs = [i.lower() for i in user_locs]

    if "all" in user_locs:
        return True
    
    if node_loc in user_locs:
        return True

    return False

def map_storage_fw_to_version(fw_hash):
    with open(os.environ["STORAGE_FW_VERS_DB"]) as vers_csv:
        vers_reader = csv.reader(vers_csv, delimiter=',')
        for row in vers_reader:
            v_num    = row[0]
            hash_val = row[1]

            if fw_hash == hash_val:
                return v_num

def compare_versions(usr_version, node_version):
    '''
        Check if node version is greater than or equal to user
        provided version
    '''
    if not usr_version:
        return False
    if node_version >= usr_version:
        return True
    
    return False

def get_latest_storage_fw_version():
    greatest = 0
    with open(os.environ["STORAGE_FW_VERS_DB"]) as vers_csv:
        vers_reader = csv.reader(vers_csv, delimiter=',')
        for row in vers_reader:
            if int(row[0]) > greatest:
                greatest = int(row[0])

    return greatest            

def check_node_fw(user_fws, node_fw):
    '''
        - user_fws is a list of firmware versions represented by their hashes
            - map firmware hash to version number from a database
        - node_fw is
            - node hash
    '''
    node_fw = map_storage_fw_to_version(node_fw)
    latest_vers = get_latest_storage_fw_version()

    if "latest" in user_fws:
        if node_fw == latest_vers:
            return True
        else:
            return False

    user_fws = [map_storage_fw_to_version(i) for i in user_fws]
    user_fws = [compare_versions(i, node_fw) for i in user_fws]

    if True in user_fws:
        return True

    return False        

def check_usr_identity(usr_identity):
    '''
        Reads a list of identities from disk and compares each with
        usr_identity
    '''
    identity_file = open(os.environ["IDENTITY_FILE"], "r")

    while True:
        line = identity_file.readline().rstrip()

        if not line:
            break

        if line == usr_identity:
            identity_file.close()
            return True
    
    identity_file.close()
    return False

def check_node_policy_compliance(user_policy_dict, storage_node_attr_dict):
    node_loc_check = check_node_location(
        user_policy_dict["storageLocIs"],
        storage_node_attr_dict["storageLocIs"]
    )

    if not node_loc_check:
        return False
    
    node_fw_check  = check_node_fw(
        user_policy_dict["fwVersion"]["storage"],
        storage_node_attr_dict["fwVersion"]["storage"]
    )

    if not node_fw_check:
        return False
    
    usr_identity_check = check_usr_identity(user_policy_dict["sessionKeyIs"])

    return node_loc_check and node_fw_check and usr_identity_check

def main():
    usr_policy_json = sys.argv[1]
    storage_attr_json = sys.argv[2]

    usr_policy   = open(usr_policy_json)
    storage_attr = open(storage_attr_json)

    policy_dict       = json.load(usr_policy)
    storage_attr_dict = json.load(storage_attr)

    check_policy(policy_dict)

    if not check_node_policy_compliance(policy_dict, storage_attr_dict):
        print("Not compliant")
    else:
        print("Compliant")

if __name__ == "__main__":
    main()