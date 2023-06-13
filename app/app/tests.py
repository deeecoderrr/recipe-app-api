'''
Sample tests
'''

from django.test import SimpleTestCase
from . import calc

class CalcTests(SimpleTestCase):
    ''' Test calc module'''
    def test_add_numbers(self):
        ''' Testing add numbers '''
        res = calc.add(10,5)
        self.assertEqual(res, 15)
    
    def test_substract_numbers(self):
        ''' Testing add numbers '''
        res = calc.substract(10,15)
        self.assertEqual(res, 5)

