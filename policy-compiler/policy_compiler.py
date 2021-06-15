import sys
import json

from policy_checker import check_policy

def obtain_key_val(pol_pred):
    start = pol_pred.find("(")
    if start == -1:
        return None
    
    end = pol_pred.find(")")
    if end == -1:
        return None
    
    key = pol_pred[:start]
    val = pol_pred[start + 1: end]

    return (key, val)


def compile_policy(user_policy):
    '''
        Policy predicates are separated by '&' or '|'.
        However, only same policy predicates can be combined with a '|'
        and only different policy predicates can be combined with a '&'
        Hence, it makes sense to just replace '&' or '|' by a common symbol.
    '''
    user_policy = user_policy.rstrip()
    user_policy = user_policy.replace("&", "|")
    user_policy = user_policy.rstrip().split("|")
    user_dict = {}
    
    for i in user_policy:
        kv_pair = obtain_key_val(i)
        if kv_pair == None:
            return None
        
        if kv_pair[0] not in user_dict:
            user_dict[kv_pair[0]] = []
            user_dict[kv_pair[0]].append(kv_pair[1])
        else:
            user_dict[kv_pair[0]].append(kv_pair[1])
    
    if "storageFwVersionIs" in user_dict:
        user_dict["fwVersion"] = {}
        user_dict["fwVersion"]["storage"] = user_dict["storageFwVersionIs"]
        del user_dict["storageFwVersionIs"]

    user_dict["sessionKeyIs"] = user_dict["sessionKeyIs"][0]
    user_dict["query"] = user_dict["query"][0]
    
    return user_dict

def main():
    user_policy = sys.argv[1]
    user_policy = open(user_policy)
    user_policy = user_policy.readline().rstrip()

    target = sys.argv[2]
    target = open(target)
    target = json.load(target)

    result = compile_policy(user_policy)

    print(result)
    print(target)

    print(result == target)

if __name__ == "__main__":
    main()