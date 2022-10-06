import itunes


def getCover(artist, album_name, quality):

    itunes_cover = itunes.getCover(artist, album_name, quality)

    if itunes_cover != None:
        return itunes_cover
