"""
Basic usage example for Playfast.

This example demonstrates:
1. Getting single app information
2. Displaying app details
3. Using AsyncClient (recommended for best performance)

Performance: AsyncClient is 15x faster than synchronous approaches!
"""

import asyncio

from playfast import AsyncClient


async def main() -> None:
    """Main example function."""
    print("=== Playfast Basic Example ===")
    print("Using AsyncClient (15x faster than sequential!)\n")

    async with AsyncClient() as client:
        # Get app information
        print("Fetching app information for Spotify...")
        try:
            app = await client.get_app("com.spotify.music")

            # Display app details
            print(f"\n📱 {app.title}")
            print(f"👨‍💻 Developer: {app.developer}")
            print(f"⭐ Rating: {app.score} ({app.ratings:,} ratings)")
            print(f"💰 Price: ${app.price} {app.currency}")
            print(f"📂 Category: {app.category or 'N/A'}")
            print(f"🔢 Version: {app.version or 'N/A'}")
            print(f"📅 Updated: {app.updated or 'N/A'}")
            print(f"📥 Installs: {app.installs or 'N/A'}")
            print(f"🎯 Rating Category: {app.rating_category()}")
            print(f"✅ Free: {app.is_free}")

            if app.description:
                print(f"\n📝 Description (first 200 chars):")
                print(f"   {app.description[:200]}...")

            if app.screenshots:
                print(f"\n📸 Screenshots: {len(app.screenshots)} available")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
