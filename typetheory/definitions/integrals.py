'''
Created on 2 Aug 2017

@author: bsdz
'''

from ..expressions import IntegralSymbol
   
integral = IntegralSymbol('Integral', latex_repr=r'\int')
sum_ = IntegralSymbol('Sum', latex_repr=r'\sum')
product = IntegralSymbol('Product', latex_repr=r'\prod')
