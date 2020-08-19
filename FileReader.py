# FileReader
#
#   no size limiting, no chunking, very simple
#


class FileReader():
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.file = None

    def isOpen(self):
        return (self.file is not None)

    def open(self):
        try:
            self.file = open(self.filename, 'rb')
        except Exception as err:
            print(f'error opening {self.filename}: {err}')

    def listen(self):
        try:
            self.readbuffer = self.file.read() 
        except Exception as e:
            print("Exception " + e + " while reading from file")

        return self.readbuffer
