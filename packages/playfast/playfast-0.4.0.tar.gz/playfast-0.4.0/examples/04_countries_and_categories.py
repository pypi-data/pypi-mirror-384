"""Example 4: Working with Countries and Categories

Playfast provides powerful country/region utilities:
- Unique region system (162 countries → 36 unique stores)
- Region representatives for optimized data collection
- All country codes and categories
"""

from playfast import (
    fetch_apps,
    get_countries,
    get_countries_in_region,
    get_representative_country,
    get_unique_countries,
    is_unique_region,
)
from playfast.constants import Category, Collection


def example_all_countries():
    """Show all available countries."""
    print("=== Example 1: All Countries ===\n")

    countries = get_countries()

    print(f"Total countries available: {len(countries)}")
    print("\nSample countries:")
    for country in list(countries)[:10]:
        print(f"  {country.code.upper()}: {country.name}")


def example_unique_countries():
    """Show unique Play Store regions (optimized collection)."""
    print("\n=== Example 2: Unique Countries (36 stores) ===\n")

    unique_countries = get_unique_countries()

    print(f"Total unique Play Store regions: {len(unique_countries)}")
    print("\nThese countries have unique app stores:")
    for country in list(unique_countries)[:10]:
        print(f"  {country.code.upper()}: {country.name}")


def example_representative_countries():
    """Use representative countries for each region."""
    print("\n=== Example 3: Representative Countries ===\n")

    # Instead of fetching from 162 countries, fetch from 36 representatives
    representatives = [
        get_representative_country(region)
        for region in [
            "us", "kr", "jp", "de", "fr", "gb", "br", "in",
            "ru", "mx", "tr", "id", "th", "vn", "ph", "eg"
        ]
    ]

    print(f"Using {len(representatives)} representative countries:")
    for rep_code in representatives:
        print(f"  {rep_code.upper()}")


def example_region_mapping():
    """Check region mapping."""
    print("\n=== Example 4: Region Mapping ===\n")

    # Check if countries share the same store
    test_countries = ["us", "gb", "de", "at", "ch"]

    print("Checking which countries have unique stores:")
    for code in test_countries:
        rep = get_representative_country(code)
        is_unique = is_unique_region(code)
        print(f"  {code.upper()}: unique={is_unique}, representative={rep.upper()}")


def example_countries_in_region():
    """Show all countries in a region."""
    print("\n=== Example 5: Countries in Region ===\n")

    # Germany represents several European countries
    de_countries = get_countries_in_region("de")

    print(f"Countries sharing Germany's Play Store ({len(de_countries)}):")
    for country in de_countries:
        print(f"  {country.code.upper()}: {country.name}")


def example_categories():
    """Show all available categories."""
    print("\n=== Example 6: Categories ===\n")

    print("Available categories:")
    categories = [
        Category.GAME_ACTION,
        Category.GAME_CASUAL,
        Category.GAME_STRATEGY,
        Category.SOCIAL,
        Category.COMMUNICATION,
        Category.PRODUCTIVITY,
        Category.ENTERTAINMENT,
        Category.MUSIC_AND_AUDIO,
        Category.VIDEO_PLAYERS,
        Category.PHOTOGRAPHY,
    ]

    for cat in categories:
        print(f"  {cat}")


def example_practical_use_case():
    """Practical example: Fetch top games from unique regions."""
    print("\n=== Example 7: Practical Use Case ===\n")

    # Instead of fetching from 162 countries, use 8 key representatives
    key_regions = ["us", "kr", "jp", "de", "br", "in", "ru", "id"]

    print(f"Fetching Spotify from {len(key_regions)} key regions...")

    apps_by_country = {}
    for region in key_regions:
        rep = get_representative_country(region)
        apps_by_country[rep] = rep

    # Fetch using batch API
    apps = fetch_apps(
        app_ids=["com.spotify.music"],
        countries=key_regions,
        lang="en",
    )

    print(f"\nSpotify ratings across {len(apps)} regions:")
    for app in apps:
        # Note: You'd need to match apps to countries in practice
        print(f"  {app.score}⭐ - {app.ratings:,} ratings")


def example_collections():
    """Show collection types."""
    print("\n=== Example 8: Collections ===\n")

    print("Available collections:")
    collections = [
        Collection.TOP_FREE,
        Collection.TOP_PAID,
        Collection.TOP_GROSSING,
        Collection.TOP_NEW_FREE,
        Collection.TOP_NEW_PAID,
        Collection.MOVERS_SHAKERS,
    ]

    for coll in collections:
        print(f"  {coll}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Countries and Categories Examples")
    print("=" * 60)

    example_all_countries()
    example_unique_countries()
    example_representative_countries()
    example_region_mapping()
    example_countries_in_region()
    example_categories()
    example_practical_use_case()
    example_collections()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("\nKey Takeaways:")
    print("  ✓ 162 countries → 36 unique Play Stores")
    print("  ✓ Use get_unique_countries() for optimized collection")
    print("  ✓ Use get_representative_country() for region mapping")
    print("  ✓ Categories and Collections are available as enums")
    print("=" * 60)


if __name__ == "__main__":
    main()
