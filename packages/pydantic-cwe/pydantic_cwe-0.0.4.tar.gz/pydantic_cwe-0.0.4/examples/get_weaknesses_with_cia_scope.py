from pydantic_cwe.loader import Loader

_loader = Loader()

catalog = _loader.load()

TARGET_VULNERABILITY_MAPPINGS = ['Allowed-with-Review', 'Allowed']

CIA_SCOPE = ["Confidentiality", "Integrity", "Availability"]

cia_weaknesses = []

for weakness in catalog.get_ordered_weaknesses():
    if weakness.status == 'Deprecated':
        continue

    if weakness.mapping_notes['Usage'] not in TARGET_VULNERABILITY_MAPPINGS:
        continue

    weakness_scope = weakness.get_consequences_scope()

    # drop "Other" from the scope

    if "Other" in weakness_scope:
        weakness_scope.remove("Other")

    if not weakness_scope:
        continue

    # check if weakness_scope is a subset of CIA_SCOPE
    if set(weakness_scope).issubset(CIA_SCOPE):
        cia_weaknesses.append(weakness.id)


print(cia_weaknesses)
print(f"Total number weaknesses within the CIA scope: {len(cia_weaknesses)}")
