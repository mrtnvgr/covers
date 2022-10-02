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

        self.statistics = {"skipped": 0, "converted": 0, "new": 0}
        self.not_found = []

        self.checkFolders()

    def checkFolders(self):
        # Get folder from arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("-f", "--folder", required=True, help="folder path")
        parser.add_argument(
            "--force", help="always overwrite file covers", action="store_true"
        )
        parser.add_argument("-s", "--size", type=int, default=1000, help="cover size")
        parser.add_argument(
            "--keep-size", action="store_true", help="do not resize covers"
        )
        parser.add_argument(
            "--format",
            default="jpeg",
            choices=("jpeg", "png"),
            help="cover image format",
        )
        parser.add_argument(
            "--no-stat", action="store_true", help="do not print statistics"
        )
        parser.add_argument("--verbose", action="store_true", help="verbose output")
        self.args = parser.parse_args()

        # Check if argument is folder and exists
        if os.path.exists(self.args.folder) and os.path.isdir(self.args.folder):

            audiopaths = []

            # Get paths with audio

            # Iterate through folders
            for currentpath, folders, files in os.walk(self.args.folder):

                # Iterate through files
                for file in files:

                    # Check if file extension is ext
                    if self.checkAudio(file):
                        self.lenf += 1

                        if currentpath != None:
                            audiopaths.append(currentpath)
                            currentpath = None

            # Iterate through folders
            for path in audiopaths:
                self.cover(path)

        print()

        # Check if statistics is not blocked
        if not self.args.no_stat:

            # Print statistics
            print()
            print("Covers statistics:")
            print(f"  -  Skipped: {self.statistics['skipped']}")
            print(f"  -  Converted: {self.statistics['converted']}")
            print(f"  -  New: {self.statistics['new']}")
            print(f"  -  Not Found: {len(self.not_found)}")
            print()

            # Check if not_found list contains any folders

            if self.not_found != []:

                # Print paths where covers were not found
                print("Covers were not found in:")

                for folder in self.not_found:
                    print(f"  -  {folder}")

                print()

    def cover(self, path):

        cover = None
        files = os.listdir(path)

        # List of cover names (from most to least possible)
        names = ("cover", "folder", "front", ".png", ".jpg")

        # Iterate through possible names
        for name in names:

            # Check if file is in path
            cover_path = self.fileExists(path, name)
            if cover_path != None:

                # Get cover image
                cover = self.getCover(cover_path)

                # Stop iterating if cover found
                if cover:
                    break

        for file in files:

            if self.checkAudio(file):
                file_path = os.path.join(path, file)
                self.addCover(cover, file_path)

                self.print(f"[{self.curf}/{self.lenf}] {file_path}")

                self.curf += 1

    def getCover(self, cover_path):

        resized = False

        cover = Image.open(cover_path).convert("RGB")

        # Check if resizing is allowed
        if not self.args.keep_size:

            shape = self.getShape(cover.size)

            # Check if cover is square
            if shape == "square":

                size = (self.args.size, self.args.size)

            elif shape == "rectangle":

                # Get size factor
                factor = max(cover.size) / min(cover.size)

                # Get normalized size
                size = [self.args.size, self.args.size]

                # Get max value index
                index = cover.size.index(max(cover.size))

                # Multiply value by factor, index = max value from cover size
                size[index] = int(size[index] * factor)

            else:

                # Unexpected behaviour
                print(f"err: {shape}")
                exit(1)

            # Check if size and cover argument size differ
            if cover.size != size:
                cover = cover.resize(
                    size,
                    Image.Resampling.BICUBIC,
                )
                resized = True

        output = BytesIO()
        cover.save(output, format=self.args.format.capitalize())

        return output.getvalue(), resized

    def addCover(self, cover, file_path):
        if os.path.isfile(file_path):

            audio = mutagen.File(file_path)
            if audio != None and hasattr(audio, "pictures"):

                # File has not pictures
                if audio.pictures == [] and cover != None:

                    pic = self.createPicture(cover)

                    audio.clear_pictures()

                    audio.add_picture(pic)

                    audio.save(file_path)

                    # Update statistics
                    self.statistics["new"] += 1

                # File has pictures
                else:

                    # Check picture size
                    newPictures = []
                    resized_fuse = False

                    for picture in audio.pictures:

                        picdata = picture.data
                        # Check picture size
                        if (
                            picture.width != self.args.size
                            or picture.height != self.args.size
                        ) or self.args.force:

                            # Resize picture
                            picdata, resized = self.getCover(BytesIO(picdata))

                            # Burn resized fuse
                            if not resized:
                                resized_fuse = True

                        newPicture = self.createPicture(picdata)

                        newPictures.append(newPicture)

                    # Check if any pictures were resized
                    if resized_fuse:
                        audio.clear_pictures()

                        for picture in newPictures:

                            audio.add_picture(picture)

                        audio.save(file_path)

                        # Update statistics
                        self.statistics["converted"] += 1
                    else:

                        # Update statistics
                        self.statistics["skipped"] += 1

                # Update statistics if cover not found
                if audio.pictures == []:

                    # Check if path is not in not_found list
                    folder_path = os.path.dirname(file_path)
                    if folder_path not in self.not_found:
                        self.not_found.append(folder_path)

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

    @staticmethod
    def fileExists(path, name):
        for file in os.listdir(path):
            if name in file.lower() and (
                file.lower().endswith(".jpg") or file.lower().endswith(".png")
            ):
                path = os.path.join(path, file)
                return path

    @staticmethod
    def checkAudio(file):
        exts = (".flac", ".mp3", ".wav", ".m4a")
        for ext in exts:

            if file.lower().endswith(ext):
                return True
        return False

    def print(self, text):

        if self.args.verbose:
            print(text)
        else:
            print(f"\033[K{text}", end="\r")


if __name__ == "__main__":
    Main()
