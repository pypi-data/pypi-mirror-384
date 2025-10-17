"""
import itkdb
c = itkdb.Client()
from itkdb.models.component import Component
data = c.get('getComponent', json={'component': '92578da734e6abd4f7931f17735a2ecc'})
comp = Component(c, data)
comp
comp.walk()
"""
