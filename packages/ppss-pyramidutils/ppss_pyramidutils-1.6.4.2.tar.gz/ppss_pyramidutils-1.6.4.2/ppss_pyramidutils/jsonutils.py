import logging
l = logging.getLogger(__name__)

class jsonwalker:
    def __init__(self, callback, skip_keys:list = []) -> None:
        self.callback = callback
        self.skip_keys = set(skip_keys)
        #try:
        #    iterator = iter(callback)
        #    self.callback = callback
        #except TypeError:
        #    self.callback = (callback,)

    def explorelist(self, node):
        newlist = []
        for item in node:
            newlist.append(self.explore(item))
        return newlist

    def exploredict(self, node):
        struct = {}
        for k, v in node.items():
            if k in self.skip_keys:
                struct[k] = v
            else:    
                struct[k] = self.explore(v)
        return struct

    

    def explore(self, node):
        if isinstance(node, dict):
            return self.exploredict(node)
        elif isinstance(node, list):
            return self.explorelist(node)
        else:
            # return self.encryptval(node)
            return self.callback(node)

    def walk(self, thejson):
        return self.explore(thejson)