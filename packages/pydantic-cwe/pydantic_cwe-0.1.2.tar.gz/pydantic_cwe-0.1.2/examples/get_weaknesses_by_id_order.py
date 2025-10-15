from pydantic_cwe.loader import Loader

_loader = Loader()

catalog = _loader.load()

for weakness in catalog.get_ordered_weaknesses():
    if weakness.status == 'Deprecated':
        continue

    print(weakness.id, weakness.abstraction, weakness.mapping_notes['Usage'])