import sys
import json
import os

'''
userIdentity is added by the host to the dictionary
'''
policy_predicates = [
    "sessionKeyIs",
    "storageLocIs",
    "fwVersion",
    "hostQuery",
    "storageQuery",
    "userIdentity",
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
                    print(f"We do not support \"{i}\" for firmware version attributes")
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

def map_fw_to_version(fw_hash):
    pass

def compare_versions(usr_version, node_version):
    '''
        Check if node version is greater than or equal to user
        provided version
    '''
    pass

def check_node_fw(user_fws, node_fw):
    '''
        - user_fws is a list of firmware versions represented by their hashes
            - map firmware hash to version number from a database
        - node_fw is a dict containing two values
            - node fw version number
            - a boolean representing whether this is the latest value
    '''
    if "latest" in user_fws:
        if node_fw["latest"]:
            return True
        else:
            return False

    user_fws = [compare_versions(i, node_fw["version"]) for i in user_fws]

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
        storage_node_attr_dict["location"]
    )

    if not node_loc_check:
        return False

    node_fw_check  = check_node_fw(
        user_policy_dict["fwVersion"]["storage"],
        storage_node_attr_dict["fwVersion"]
    )

    if not node_fw_check:
        return False

    usr_identity_check = check_usr_identity(user_policy_dict["userIdentity"])

    return node_loc_check and node_fw_check and usr_identity_check

def main():
    policy_json = sys.argv[1]
    policy_dict = json.loads(policy_json)

    check_policy(policy_dict)

if __name__ == "__main__":
    main()