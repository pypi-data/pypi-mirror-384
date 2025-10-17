import py_dict_comparing_xethhung12 as project
from j_vault_http_client_xethhung12 import client
def main():
    client.load_to_env()
    # project.compare()
    repo = project.ComparingRepo()
    

    incidnet1 = repo.load_data("incident1",project.load_win_based_CSV("incident_2.CSV"))
    incident2 = repo.load_data("incident2",project.load_win_based_CSV("incident_3.CSV"))

    our_only, common, other_only = incidnet1.match_header(incident2)
    print(our_only)
    print(common)
    print(other_only)

    found_count, not_found_count, found,not_found = incidnet1.matching_keys(incident2, common)
    print(incidnet1.original_index([i for key in found for i in key['our']]))
    print(incidnet1.original_index([i for key in not_found for i in key['our']]))

    print(incidnet1.take_lines([1,2]))

