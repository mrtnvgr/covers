import requests
import re


def downloadCover(url):

    # Get bytes from url
    return requests.get(url, headers=headers).content


def cleanAlbumName(name):

    substitutions = {
        " - .*": "",
        r" \[.*\]": "",
        r" \(.*\)": "",
    }
    for (key, value) in substitutions.items():
        name = re.sub(key, value, name, flags=re.IGNORECASE)

    return name.lower()
