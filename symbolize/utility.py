'''utility: useful methods and classes

symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

# https://stackoverflow.com/questions/8544983/dynamically-mixin-a-base-class-to-an-instance-in-python
#
def extend_instance(obj, cls):
    """Apply mixins to a class instance after creation"""
    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type(base_cls_name, (base_cls, cls),{})
    

def generate_random_string(n):
    import random,string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

class ToBeImplemented(Exception): pass