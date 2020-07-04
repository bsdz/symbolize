"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""
from ..expressions import IntegralSymbol

integral = IntegralSymbol("∫", latex_repr=r"\int")
sum_ = IntegralSymbol("∑", latex_repr=r"\sum")
product = IntegralSymbol("∏", latex_repr=r"\prod")
