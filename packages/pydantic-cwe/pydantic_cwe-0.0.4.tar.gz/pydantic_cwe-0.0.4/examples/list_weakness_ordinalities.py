from pydantic_cwe.loader import Loader

_loader = Loader()
catalog = _loader.load()

for weakness in catalog.get_ordered_weaknesses():
    if weakness.ordinalities:
        _ords = weakness.get_ordinalities()

        print(f"CWE-{weakness.id}", "Weakness Ordinalities:", _ords)
