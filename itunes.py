import requests
import urllib.parse

import util

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36"
}


def getCover(artist, album_name, quality):

    # Search for artist albums
    search_data = urllib.parse.urlencode(
        {"term": artist, "media": "music", "entity": "album"}
    )

    try:
        response = requests.get(
            f"https://itunes.apple.com/search?{search_data}", headers=headers
        )
    except requests.exceptions.ConnectionError:
        print("WARNING: No internet connection. Use --local argument")
        return

    # Check if result is not an error
    if response.status_code == 200:

        # Get json data
        data = response.json()

        # Check for any albums
        if data["resultCount"] != "0":

            cover = searchAlbum(data["results"], album_name)

            if cover:

                # Get cover url from cover results
                cover_url = cover.get("artworkUrl100", None)

                # Check that the cover url is found
                if cover_url:

                    # Get best quality
                    cover_url = cover_url.replace("100x100bb", f"{quality}x{quality}bb")

                    # Return cover info
                    return {
                        "artist": cover["artistName"],
                        "title": cover["collectionName"],
                        "bytes": util.downloadCover(cover_url),
                    }


def searchAlbum(albums, album_name):

    # Iterate through albums in reversed order
    for album in albums:

        # Fallback checks
        if album.get("collectionName", None):

            # Match
            if util.cleanAlbumName(album["collectionName"]) == util.cleanAlbumName(
                album_name
            ):

                # Return
                return album
