import StringIO

def initTextStream():
    return TextStream()

class TextStream(StringIO.StringIO):
    def str(self):
        return self.getvalue()
