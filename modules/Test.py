__version__     = '0.0.1'

class Test:
    def __init__(self, continueBool):
        if continueBool: 
            print "Running Test"
        
    def run(self):
        return {"success": True} 

    def get_version(self):
        return __version__
