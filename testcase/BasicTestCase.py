#encoding:utf-8
'''
Created on 2014-8-13

@author: 张文硕
'''
import unittest


class Test(unittest.TestCase):
    def test_1(self):
        import hhplt.gs10
        import hhplt.testengine.product_manage
        
        print `hhplt.testengine.product_manage.productTestSuits`



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
