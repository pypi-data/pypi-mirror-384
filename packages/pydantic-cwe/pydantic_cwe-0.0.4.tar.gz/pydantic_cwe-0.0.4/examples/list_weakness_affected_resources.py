from pydantic_cwe.loader import Loader

_loader = Loader()

catalog = _loader.load()


for weakness in catalog.get_ordered_weaknesses():
    if weakness.affected_resources:
        af = weakness.affected_resources["Affected_Resource"]

        if not isinstance(af, list):
            af = [af]

        print(f"CWE-{weakness.id}", "Affected Resources:", af)
