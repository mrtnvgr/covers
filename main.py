#!/usr/bin/env python

from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


from io import BytesIO
import mutagen
import argparse
import os


class Main:
    def __init__(self):

        # Set cover info
        self.coverinfo = {"size": 1000, "format": "jpeg"}

        self.curf = 1

        self.checkFolders()

    def checkFolders(self):
        # Get folder from arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--folder", required=True)
        parser.add_argument(
            "--force", help="always overwrite file covers", action="store_true"
        )
        self.args = parser.parse_args()

        # Check if folder exists
        if os.path.exists(self.args.folder):

            audiopaths = []
            self.lenf = 0

            # Get paths with audio

            # Iterate through folders
            for currentpath, folders, files in os.walk(self.args.folder):

                # Iterate through files
                for file in files:

                    # Check if file extension is ext
                    if (
                        file.endswith(".flac")
                        or file.endswith(".mp3")
                        or file.endswith(".wav")
                    ):
                        self.lenf += 1

                        if currentpath != None:
                            audiopaths.append(currentpath)
                            currentpath = None


            for path in audiopaths:
                self.cover(path)
        print()

    def cover(self, path):

        cover = None
        files = os.listdir(path)

        for file in files[:]:
            if "cover" in file.lower() or "folder" in file.lower():

                cover_path = os.path.join(path, file)
                cover = self.getCover(cover_path)

                files.remove(file)

                break

        if cover:

            for file in files:

                file_path = os.path.join(path, file)
                self.addCover(cover, file_path)
                print(f"\033[K[{self.curf}/{self.lenf}] {file_path}", end="\r")

                self.curf += 1

    def getCover(self, cover_path):

        try:
            cover = Image.open(cover_path).convert("RGB")
        except:
            return

        if cover.size != (self.coverinfo["size"], self.coverinfo["size"]):
            cover = cover.resize(
                (self.coverinfo["size"], self.coverinfo["size"]),
                Image.Resampling.BICUBIC,
            )

        output = BytesIO()
        cover.save(output, format=self.coverinfo["format"].capitalize())

        return output.getvalue()

    def addCover(self, cover, file_path):
        if os.path.isfile(file_path):

            audio = mutagen.File(file_path)

            if audio != None and hasattr(audio, "pictures"):

                # File has not pictures
                if audio.pictures == []:

                    pic = self.createPicture(cover)

                    audio.clear_pictures()

                    audio.add_picture(pic)

                    audio.save(file_path)

                # File has pictures
                else:

                    # Check picture size
                    newPictures = []
                    for picture in audio.pictures:

                        # Check picture size
                        if (
                            picture.width != self.coverinfo["size"]
                            and picture.height != self.coverinfo["size"]
                        ) or self.args.force:

                            # Resize picture
                            newData = self.getCover(BytesIO(picture.data))

                            newPicture = self.createPicture(newData)

                            newPictures.append(newPicture)

                    audio.clear_pictures()

                    for picture in newPictures:

                        audio.add_picture(picture)

                    audio.save(file_path)

    def createPicture(self, data):
        pic = mutagen.flac.Picture()

        pic.data = data

        pic.type = mutagen.id3.PictureType.COVER_FRONT
        pic.mime = "image/" + self.coverinfo["format"]
        pic.width = self.coverinfo["size"]
        pic.height = self.coverinfo["size"]
        pic.depth = 16

        return pic


if __name__ == "__main__":
    Main()
