from pydantic_cwe.loader import Loader

def main():
    # Create a loader instance
    loader = Loader()
    
    try:
        # Load the catalog
        catalog = loader.load()
        
        # Print some basic information about the catalog
        print(f"Catalog Name: {catalog.name}")
        print(f"Catalog Version: {catalog.version}")
        print(f"Catalog Date: {catalog.date}")
        print(f"Number of weaknesses: {len(catalog.weaknesses.weaknesses)}")
        
        # Print information about the first weakness
        if catalog.weaknesses.weaknesses:
            first_weakness = catalog.weaknesses.weaknesses[0]
            print("\nFirst Weakness:")
            print(f"ID: {first_weakness.id}")
            print(f"Name: {first_weakness.name}")
            print(f"Abstraction: {first_weakness.abstraction}")
            print(f"Structure: {first_weakness.structure}")
            print(f"Status: {first_weakness.status}")
            print(f"Description: {first_weakness.description}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()