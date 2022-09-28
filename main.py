#!/usr/bin/env python

from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


from io import BytesIO
import mutagen
import argparse
import os


class Main:
    def __init__(self):

        self.curf = 1
        self.lenf = 0

        self.checkFolders()

    def checkFolders(self):
        # Get folder from arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--folder", required=True)
        parser.add_argument(
            "--force", help="always overwrite file covers", action="store_true"
        )
        parser.add_argument("-s", "--size", type=int, default=1000, help="cover size")
        parser.add_argument("--format", default="JPEG", help="cover image format")
        self.args = parser.parse_args()

        # Check if folder exists
        if os.path.exists(self.args.folder):

            audiopaths = []

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

        # Check if cover is square
        if self.getShape(cover.size) == "square":

            # Check if picture size and cover size differ
            if cover.size != (self.args.size, self.args.size):
                cover = cover.resize(
                    (self.args.size, self.args.size),
                    Image.Resampling.BICUBIC,
                )

        output = BytesIO()
        cover.save(output, format=self.args.format.capitalize())

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

                        picdata = picture.data

                        # Check picture size
                        if (
                            picture.width != self.args.size
                            and picture.height != self.args.size
                        ) or self.args.force:

                            # Check if cover is square
                            if self.getShape(cover.size) == "square":

                                # Resize picture
                                picdata = self.getCover(BytesIO(picdata))

                        newPicture = self.createPicture(picdata)

                        newPictures.append(newPicture)

                    # Check for new pictures
                    if newPictures != []:
                        audio.clear_pictures()

                        for picture in newPictures:

                            audio.add_picture(picture)

                        audio.save(file_path)

    def createPicture(self, data):
        pic = mutagen.flac.Picture()

        pic.data = data

        pic.type = mutagen.id3.PictureType.COVER_FRONT
        pic.mime = "image/" + self.args.format
        pic.width = self.args.size
        pic.height = self.args.size
        pic.depth = 16

        return pic

    @staticmethod
    def getShape(size):
        allowable_size_error = size[0] // 10
        size_error = abs(size[0] - size[1])
        if size_error <= allowable_size_error:
            return "square"
        else:
            return "rectangle"


if __name__ == "__main__":
    Main()
