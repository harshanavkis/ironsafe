import sys
import json

policy_predicates = [
    "sessionKeyIs",
    "storageLocIs",
    "fwVersion",
    "hostQuery",
    "storageQuery",
]

fw_ver_attributes = [
    "host",
    "storage",
]

def check_policy(policy_dict):
    '''
        Check that the user submitted policy has the
        correct attributes.
    '''
    for i in policy_dict:
        if i not in policy_predicates:
            print(f"We do not support policy predicate: {i}")
            sys.exit(1)
        if i == "fwVersion":
            for j in policy_dict[i]:
                if j not in fw_ver_attributes:
                    print(f"We do not support \"{i}\" for firmware version attributes")
                    sys.exit(1)

def main():
    policy_json = sys.argv[1]
    policy_dict = json.loads(policy_json)

    check_policy(policy_dict)

if __name__ == "__main__":
    main()