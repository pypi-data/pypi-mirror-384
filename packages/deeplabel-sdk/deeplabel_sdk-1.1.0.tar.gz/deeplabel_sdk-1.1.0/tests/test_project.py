from deeplabel.projects import Project

def test_fetch_project_from_project_id(client, project_id):
    Project.from_project_id(project_id, client)

  
def test_fetch_project_from_search_params(client, project_id):    
    Project.from_search_params({"projectId":project_id}, client)


def test_get_members(client, project_id):
    project = Project.from_project_id(project_id, client)
    member = project.members