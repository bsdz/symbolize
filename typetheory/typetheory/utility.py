'''
Created on 16 Jul 2017

@author: bsdz
'''

# https://stackoverflow.com/questions/8544983/dynamically-mixin-a-base-class-to-an-instance-in-python
#
def extend_instance(obj, cls):
    """Apply mixins to a class instance after creation"""
    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type(base_cls_name, (base_cls, cls),{})