from pydantic_cwe.loader import Loader

_loader = Loader()
catalog = _loader.load()

for cwe_id, memberships in catalog.get_weakness_memberships().items():
    print(f"CWE-{cwe_id}", memberships)
