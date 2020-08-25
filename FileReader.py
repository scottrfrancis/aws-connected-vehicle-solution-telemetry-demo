# FileReader
#

import boto3

class FileReader():
    LOCAL_DIR = '/tmp'

    def __init__(self, fileURI = None):
        super().__init__()
        self.localFile = None
        self.file = None

        self.fileURI = fileURI

        self.cols = []

        self.open()

    def __del__(self):
        if self.isOpen():
            self.file.close()
            self.file = None
        

    def getFileURI(self):
        return self.fileURI

    def isOpen(self):
        return (self.file is not None)

    def _fetchFromS3(self, bucket, key):
        s3 = boto3.client('s3')

        localFile = "/".join([self.LOCAL_DIR, key])
        result = s3.download_file(bucket, key, localFile)

        self.localFile = localFile

    def _fetchFileFromURI(self):
        try:
            handlers = { 's3:': self._fetchFromS3 }
            src = self.fileURI.split("/")

            protocol = src[0]
            bucket = src[2]
            key = "/".join(src[3:])

            handlers[protocol](bucket, key)
        except Exception as err:
            pass
        
    def open(self):
        try:
            if self.localFile == None:
                self._fetchFileFromURI()

            self.file = open(self.localFile, 'r')
            header = self.file.readline()
            self.cols = header.split(",")
        except Exception as err:
            print(f'error opening {self.localFile}: {err}')

    def _makeSample(self, lineCSV):
        sample = {}
        line = lineCSV.split(",")
        for i in range(0, len(self.cols)):
            sample[self.cols[i]] = line[i]
        
        return sample

    def getSample(self):
        readbuffer = {}
        try:
            readbuffer = self._makeSample(self.file.readline())
        except Exception as e:
            print("Exception while reading from file")

        return readbuffer
