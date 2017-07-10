'''
Created on 10 Jul 2017

@author: bsdz
'''
class Renderer(object):
    def __init__(self, expression: "Expression"):
        self.expression = expression
    
    def render(self):
        raise NotImplementedError()