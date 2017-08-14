'''
Created on 2 Aug 2017

@author: bsdz
'''

from ..expressions import IntegralExpression
   
integral = IntegralExpression('Integral', latexrepr=r'\int')
sum_ = IntegralExpression('Sum', latexrepr=r'\sum')
product = IntegralExpression('Product', latexrepr=r'\prod')
