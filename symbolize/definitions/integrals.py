'''
Created on 2 Aug 2017

@author: bsdz
'''

from ..expressions import IntegralSymbol
   
integral = IntegralSymbol('∫', latex_repr=r'\int')
sum_ = IntegralSymbol('∑', latex_repr=r'\sum')
product = IntegralSymbol('∏', latex_repr=r'\prod')
