import sys
import json

TABLE_LIST = ["LINEITEM", "ORDERS", "PARTSUPP", "CUSTOMER", "PART", "SUPPLIER", "NATION", "REGION"]

CLIENT_DICT = {
    "sessionKeyIs": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCssVqLmQg7fBLBDWYPuaozWwPiHLGhLj/HOd5WfDBQvhcWeW57MV4RNndksh720GdNXA3zEpWqdaa00lcZsesy/qPkgb83scoxX9sGkzDSY6aeQ2ZN0fOn0TiO3HA/ej6sJFYoPO0GhUfYshGg7ezIVTVzxuuAXwuDwwUEwc3Q7X8+zsKTsgWA7VWIzI0CR5taVzjCEHplehxSENxIviJV3RfKxxIUJ4BlrTu8XxxzEY26T+eZyxuTlC5eD+mrP8NtloVxX9/o9MvOKD9g/IqBJK9+ppGRlhqCT2c/AMiVxEyc9i7a4UsKL0GP76OHJ0BulIqPGneqDXBzJlcNIQ3ONE9thy0CzIDQxuc3emXprRkVoD7K6p4yWSgi0wf7RkeCzff2hnE+YecWFgORjJUt3S4GTmJuJCffxXZ3c9+ULhy46OWR6N7QJuUULPOvyIdClU72KpGgiVkid5u1XwgrpyPKVnp+SmRUmArS9p/90GO9RobpSKVlTHxWKnfi8zj6tDt8x9gs/d8rolkz0hFISBi8xbXAsgJT+m6hEzdMN8FG1yOeE7M0F0S6CURASKwuYut4yzcr5mENmk/o4MnCUY5owp+evgYwm44usL5ntCND/txLpUdlRLo5BQtc8fVlZ61JNxThiIrgQVtUxsc70O0YmfGcLepawiJdXMKYFQ== hvub@hack-haven",
    "query": "select * from lineitem;"
}

def read_user_data_access_policy():
    user_data_policy = open(sys.argv[2])
    user_data_policy = json.load(user_data_policy)

    return user_data_policy

def run_timely_deletion_case(client_dict):
    user_data_policy = read_user_data_access_policy()
    if client_dict["sessionKeyIs"] not in user_data_policy["sessionKeyIs"]:
        return False
    query = client_dict["query"].lower()
    
    for i in TABLE_LIST:
        query = query.replace(i.lower(), "(select * from {} where expiry_date >= \'{}\')".format(i.lower(), user_data_policy["expiryDate"]))
    return query

def main():
    if sys.argv[1] == "1":
        print(run_timely_deletion_case(CLIENT_DICT))
      

if __name__ == "__main__":
    main()