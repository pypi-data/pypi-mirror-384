import pytest
from  deeplabel.client import DeeplabelClient


@pytest.fixture(scope="session")
def client():
    token = "insert token here"
    client = DeeplabelClient(token=token, restriction=False)
    return client

@pytest.fixture(scope="session")
def project_id():
    project_id = "635a32f66a9ded001ea0b912"
    return project_id

