from pydantic_cwe.loader import Loader

_loader = Loader()
catalog = _loader.load()

for category in catalog.get_ordered_categories():
    if category.name.startswith("Comprehensive Categorization"):
        print(category.id, category.name, category.get_weakness_ids())
