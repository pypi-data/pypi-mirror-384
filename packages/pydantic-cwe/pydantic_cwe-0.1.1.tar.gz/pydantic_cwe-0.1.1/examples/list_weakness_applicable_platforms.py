from pydantic_cwe.loader import Loader

_loader = Loader()

catalog = _loader.load()


for weakness in catalog.get_ordered_weaknesses():
    if weakness.applicable_platforms:
        _aps = {}
        for k, v in weakness.applicable_platforms.items():
            if isinstance(v, dict):
                name = [v["Name"] if "Name" in v else v["Class"]]
            else:
                name= [el["Name"] if "Name" in el else el["Class"] for el in v]

            _aps[k] = name if len(name) > 1 else name[0]

        print(f"CWE-{weakness.id}", "Applicable Platforms:", _aps)
