from pydantic_cwe.loader import Loader

_loader = Loader()

catalog = _loader.load()


for weakness in catalog.get_ordered_weaknesses():
    if weakness.functional_areas:
        fa = weakness.functional_areas["Functional_Area"]

        if not isinstance(fa, list):
            fa = [fa]

        print(f"CWE-{weakness.id}", "Functional Areas:", fa)
