# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 21:24:52 2020
@author: hansb
"""

import unittest as unittest

def import_local():
    """
    In order to be able to run our tests manually from the 'tests' directory
    we force import from the local package.
    """
    me = "cdxcore"
    import os
    import sys
    cwd = os.getcwd()
    if cwd[-len(me):] == me:
        return
    assert cwd[-5:] == "tests",("Expected current working directory to be in a 'tests' directory", cwd[-5:], "from", cwd)
    assert cwd[-6] in ['/', '\\'],("Expected current working directory 'tests' to be lead by a '\\' or '/'", cwd[-6:], "from", cwd)
    sys.path.insert( 0, cwd[:-6] )
import_local()
    
"""
Imports
"""
from cdxcore.subdir import SubDir, CacheMode, VersionError, VersionPresentError, VersionedCacheRoot
from cdxcore.version import version
import numpy as np

class Test(unittest.TestCase):

    def test_subdir(self):

        sub = SubDir("?/.tmp_test_for_cdxbasics.subdir", delete_everything=True )
        sub['y'] = 2
        sub.write('z',3)
        sub.write_string('l',"hallo")
        sub.write(['a','b'],[11,22])

        lst = str(sorted(sub.files()))
        self.assertEqual(lst, "['a', 'b', 'y', 'z']")
        lst = str(sorted(sub.files(ext="txt")))
        self.assertEqual(lst, "['l']")

        # test naming
        self.assertEqual( str(sub), sub.path + ";*" + sub.ext )
        self.assertEqual( repr(sub), "SubDir(" + sub.path + ";*" + sub.ext + ")" )

        # read them all back
        self.assertEqual(sub['y'],2)
        self.assertEqual(sub['z'],3)
        self.assertEqual(sub.read_string('l'),"hallo")
        self.assertEqual(sub['a'],11)
        self.assertEqual(sub['b'],22)
        self.assertEqual(sub(['a','b'], None), [11,22])
        self.assertEqual(sub.read(['a','b']), [11,22])
        self.assertEqual(sub[['a','b']], [11,22])
        self.assertEqual(sub(['aaaa','bbbb'], None), [None,None])

        # test alternatives
        self.assertEqual(sub.read('y'),2)
        self.assertEqual(sub.read('y',None),2)
        self.assertEqual(sub.read('u',None),None)
        self.assertEqual(sub('y',None),2)
        self.assertEqual(sub('u',None),None)

        # missing objects
        with self.assertRaises(AttributeError):
            print(sub.x2)
        with self.assertRaises(KeyError):
            print(sub['x2'])
        with self.assertRaises(KeyError):
            print(sub.read('x2',raise_on_error=True))

        # delete & confirm they are gone
        del sub['y']
        sub.delete('z')

        del sub['x'] # silent
        with self.assertRaises(KeyError):
            sub.delete('x',raise_on_error=True)

        # sub dirs
        sub = SubDir("!/.tmp_test_for_cdxbasics.subdir", delete_everything=True )
        s1 = sub("subDir1")
        s2 = sub("subDir2/")
        s3 = SubDir("subDir3/",parent=sub)
        s4 = SubDir("subDir4", parent=sub)
        self.assertEqual(s1.path, sub.path + "subDir1/")
        self.assertEqual(s2.path, sub.path + "subDir2/")
        self.assertEqual(s3.path, sub.path + "subDir3/")
        self.assertEqual(s4.path, sub.path + "subDir4/")
        lst = str(sorted(sub.sub_dirs()))
        self.assertEqual(lst, "[]")
        sub = SubDir("!/.tmp_test_for_cdxbasics.subdir", delete_everything=True )
        s1 = sub("subDir1", create_directory=True)
        s2 = sub("subDir2/", create_directory=True)
        s3 = SubDir("subDir3/",parent=sub, create_directory=True)
        s4 = SubDir("subDir4", parent=sub, create_directory=True)
        self.assertEqual(s1.path, sub.path + "subDir1/")
        self.assertEqual(s2.path, sub.path + "subDir2/")
        self.assertEqual(s3.path, sub.path + "subDir3/")
        self.assertEqual(s4.path, sub.path + "subDir4/")
        lst = str(sorted(sub.sub_dirs()))
        self.assertEqual(lst, "['subDir1', 'subDir2', 'subDir3', 'subDir4']")

        sub.delete_all_content()
        self.assertEqual(len(sub.files()),0)
        self.assertEqual(len(sub.sub_dirs()),0)
        sub.delete_everything()

        # test vectors
        sub = SubDir("!/.tmp_test_for_cdxbasics.subdir", delete_everything=True )
        sub[['y','z']] = [2,3]

        self.assertEqual(sub[['y','z']], [2,3])
        with self.assertRaises(KeyError):
            self.assertEqual(sub[['y','z','r']], [2,3,None])
        self.assertEqual(sub.read(['y','r'],default=None), [2,None])
        self.assertEqual(sub(['y','r'],default=None), [2,None])

        sub.write(['a','b'],1)
        self.assertEqual(sub.read(['a','b']),[1,1])
        with self.assertRaises(ValueError):
            sub.write(['x','y','z'],[1,2])
        sub.delete_everything()

        # test setting ext
        sub1 = "!/.tmp_test_for_cdxbasics.subdir"
        fd1  = SubDir(sub1).path
        sub  = SubDir("!/.tmp_test_for_cdxbasics.subdir/test;*.bin", delete_everything=True )
        self.assertEqual(sub.path, fd1+"test/")
        fn   = sub.full_file_name("file")
        self.assertEqual(fn,fd1+"test/file.bin")
        sub.delete_everything()

        # test versioning
        sub = SubDir("!/.tmp_test_for_cdxbasics.subdir")
        version = "1.0.0"
        sub.write("test", "hans", version=version )
        r = sub.read("test", version=version )
        self.assertEqual(r, "hans")
        r = sub.read("test", "nothans", version="2.0.0", delete_wrong_version=False )
        self.assertEqual(r, "nothans")
        self.assertTrue(sub.exists("test"))
        r = sub.is_version("test", version=version )
        self.assertTrue(r)
        r = sub.is_version("test", version="2.0.0" )
        self.assertFalse(r)
        r = sub.read("test", "nothans", version="2.0.0", delete_wrong_version=True )
        self.assertFalse(sub.exists("test"))
        sub.delete_everything()

        # test JSON
        x = np.ones((10,))
        sub = SubDir("!/.tmp_test_for_cdxbasics.subdir", fmt=SubDir.JSON_PICKLE )
        sub.write("test", x)
        r = sub.read("test", None, raise_on_error=True)
        r = sub.read("test", None)
        self.assertEqual( list(x), list(r) )
        self.assertEqual(sub.ext, ".jpck")
        sub.delete_everything()

        sub = SubDir("!/.tmp_test_for_cdxbasics.subdir", fmt=SubDir.JSON_PLAIN )
        sub.write("test", x)
        r = sub.read("test", None)
        self.assertEqual( list(x), list(r) )
        self.assertEqual(sub.ext, ".json")
        sub.delete_everything()

        sub = SubDir("!/.tmp_test_for_cdxbasics.subdir", fmt=SubDir.BLOSC )
        sub.write("test_2", x)
        r = sub.read("test_2", None, raise_on_error=True )
        self.assertEqual( list(x), list(r) )
        self.assertEqual(sub.ext, ".zbsc")
        sub.write("test", x, version="1")
        r = sub.read("test", None, version="1")
        self.assertEqual( list(x), list(r) )
        with self.assertRaises(VersionError):
            r = sub.read("test", None, version="2", raise_on_error=True)
            # wrong version
        sub.delete_everything()

        sub = SubDir("!/.tmp_test_for_cdxbasics.subdir", fmt=SubDir.GZIP )
        sub.write("test", x)
        r = sub.read("test", None )
        self.assertEqual( list(x), list(r) )
        self.assertEqual(sub.ext, ".pgz")
        sub.write("test", x, version="1")
        r = sub.read("test", None, version="1")
        self.assertEqual( list(x), list(r) )
        with self.assertRaises(VersionError):
            r = sub.read("test", None, version="2", raise_on_error=True)
            # wrong version
        
    def test_new(self):
        subdir0 = SubDir("my_directory")      # relative to current working directory
        subdir1 = SubDir("./my_directory")    # relative to current working directory
        subdir2 = SubDir("~/my_directory")    # relative to home directory
        subdir3 = SubDir("!/my_directory")    # relative to default temp directory

        subdir11 = SubDir("my_directory", ".")      # relative to home directory
        subdir22 = SubDir("my_directory", "~")      # relative to default temp directory
        subdir33 = SubDir("my_directory", "!")      # relative to current directory
        subdir44 = SubDir("my_directory", subdir3)  # subdir2 is relative to `subdir`
        
        
        self.assertEqual( subdir0.path, subdir11.path )
        self.assertEqual( subdir1.path, subdir11.path )
        self.assertEqual( subdir2.path, subdir22.path )
        self.assertEqual( subdir3.path, subdir33.path )
        self.assertEqual( subdir3.path + "my_directory/", subdir44.path )

        subdir1 = SubDir("?/test")
        subdir2 = SubDir("?/test")
        
        self.assertNotEqual( subdir1.path, subdir2.path )
        del subdir1, subdir2

        # extension handling
        
        subdir = SubDir("!/extension_test", fmt=SubDir.BLOSC )
        self.assertEqual( subdir.ext, ".zbsc" )
        subdir = subdir("", fmt=SubDir.GZIP )
        self.assertEqual( subdir.ext, ".pgz" )
        subdir = subdir("", fmt=SubDir.JSON_PICKLE )
        self.assertEqual( subdir.ext, ".jpck" )
        subdir = subdir("", fmt=SubDir.JSON_PLAIN )
        self.assertEqual( subdir.ext, ".json" )
        subdir = subdir("", fmt=SubDir.PICKLE )
        self.assertEqual( subdir.ext, ".pck" )

        subdir0 = SubDir("!/temp;*.bin")
        subdir1 = SubDir("!/temp", ext="bin")
        subdir2 = SubDir("!/temp", ext=".bin")
        self.assertEqual( subdir0, subdir1 )
        self.assertEqual( subdir0, subdir2 )

        with self.assertRaises(ValueError):
            subdir = SubDir("!/temp;*.bin", ext="notbin")
            
        # version
        
        version = "0.1"
        data = [12,34,56]
        
        def test_format(fmt, excset=False ):
            subdir.write("test", data,  version=version, fmt=fmt )
            _ = subdir.read("test", version=version, fmt=fmt )
            self.assertEqual( data, _ )
            with self.assertRaises(VersionError):
                _ = subdir.read("test", version="x1", fmt=fmt, raise_on_error=True )
                
            # no version error
            subdir.write("test", data, version=version, fmt=fmt )
            
            if not excset:
                # json_pickle throws no exception...
                _ = subdir.read("test", raise_on_error=True, fmt=fmt )
            else:
                with self.assertRaises(VersionPresentError):
                    _ = subdir.read("test", raise_on_error=True, fmt=fmt )

        test_format( SubDir.PICKLE, True )
        test_format( SubDir.BLOSC, True )
        test_format( SubDir.GZIP, True )
        test_format( SubDir.JSON_PICKLE )
        
        # copy constructor with overwrite
        
        d1 = SubDir("?/test_subdir", ext="e1")
        d2 = SubDir(d1)
        self.assertEqual( d1.path, d2.path )
        self.assertEqual( d1.fmt, d2.fmt )
        self.assertEqual( d1.ext, d2.ext )

        d1 = SubDir("?/test_subdir", ext="e1")
        d2 = SubDir(d1, ext="e2")
        self.assertEqual( d1.path, d2.path )
        self.assertEqual( d1.fmt, d2.fmt )
        self.assertEqual( d1.ext, ".e1" )
        self.assertEqual( d2.ext, ".e2" )

        d1 = SubDir("?/test_subdir", fmt=SubDir.BLOSC )
        d2 = SubDir(d1, fmt=SubDir.GZIP )
        self.assertEqual( d1.path, d2.path )
        self.assertEqual( d1.fmt, SubDir.BLOSC )
        self.assertEqual( d2.fmt, SubDir.GZIP )
        self.assertEqual( d1.ext, ".zbsc" )
        self.assertEqual( d2.ext, ".pgz" )

        d1 = SubDir("?/test_subdir", ext="tmp", fmt=SubDir.BLOSC )
        d2 = SubDir(d1, fmt=SubDir.GZIP )
        self.assertEqual( d1.path, d2.path )
        self.assertEqual( d1.fmt, SubDir.BLOSC )
        self.assertEqual( d2.fmt, SubDir.GZIP )
        self.assertEqual( d1.ext, ".tmp" )
        self.assertEqual( d2.ext, d1.ext )

    def test_cache_mode(self):

        on = CacheMode("on")
        gn = CacheMode("gen")
        of = CacheMode("off")
        cl = CacheMode("clear")
        up = CacheMode("update")
        ro = CacheMode("readonly")

        with self.assertRaises(KeyError):
            _ = CacheMode("OFF")

        allc = [on, gn, of, cl, up, ro]

        self.assertEqual( [ x.is_on for x in allc ], [True, False, False, False, False, False ] )
        self.assertEqual( [ x.is_gen for x in allc ], [False, True, False, False, False, False ] )
        self.assertEqual( [ x.is_off for x in allc ], [False, False, True, False, False, False ] )
        self.assertEqual( [ x.is_clear for x in allc ], [False, False, False, True, False, False ] )
        self.assertEqual( [ x.is_update for x in allc ], [False, False, False, False, True, False ] )
        self.assertEqual( [ x.is_readonly for x in allc ], [False, False, False, False, False, True ] )

        self.assertEqual( [ x.read for x in allc ],  [True, True, False, False, False, True] )
        self.assertEqual( [ x.write for x in allc ], [True, True, False, False, True, False] )
        self.assertEqual( [ x.delete for x in allc ], [False, False, False, True, True, False ] )
        self.assertEqual( [ x.del_incomp for x in allc ], [True, False, False, True, True, False ] )            

class A(object):
    def __init__(self, x):
        self.x = x
class B(object):
    def __init__(self, x):
        self.x = x
     
raw_sub = VersionedCacheRoot("?/subdir_cache_test2", exclude_arg_types=[A] )

class C(object):
    def __init__(self, x):
        self.x = x
    @raw_sub.cache("0.1")
    def f(self, y):
        return self.x*y
        
class Test2(unittest.TestCase):

    def test_cache( self ):
        
        sub = SubDir("!/xx", ext="ABC")
        self.assertEqual( sub.ext, ".ABC")

        sub = VersionedCacheRoot("?/subdir_cache_test", exclude_arg_types=[A] )

        subsub = sub("sub", ext="tst")
        x = subsub.full_file_name( "hallo")
        self.assertEqual( x[-9:], "hallo.tst" )

        @sub.cache("1.0")
        def f(x):
            return x
        
        _ = f(1)
        _ = f(1)
        self.assertTrue( f.cache_info.last_cached )

        @sub.cache("1.0")
        def g(x):
            return x
        
        # a new B object each time -> no caching
        _ = f(B(1))
        _ = f(B(2))
        self.assertFalse( f.cache_info.last_cached )

        # same B object each time -> no caching
        _ = f(B(1))
        _ = f(B(1))
        self.assertTrue( f.cache_info.last_cached )
        
        # a new A object each time -> caching, as we ignore 'A' types
        _ = f(A(1))
        _ = f(A(2))
        self.assertTrue( f.cache_info.last_cached )
        
        @sub.cache("1.0", label=lambda x: f"f({x})")
        def f(x):
            return x
        
        _ = f(1)
        self.assertEqual( f.cache_info.filename[:5], "f(1) " )
        uid, _ = f(1, return_cache_uid=True)
        self.assertEqual( uid[:5], "f(1) " )
        
        @sub.cache("1.0", uid=lambda x: f"f({x})")
        def f(x):
            return x
        
        _ = f(1)
        self.assertEqual( f.cache_info.filename, "f(1)" )
        uid, _ = f(1, return_cache_uid=True)
        self.assertEqual( uid, "f(1)" )
        
        # test member caching
        
        c = C(2.)
        _ = c.f(3)
        self.assertFalse( c.f.cache_info.last_cached )
        _ = c.f(3)
        self.assertTrue( c.f.cache_info.last_cached )
        _ = c.f(2)
        self.assertFalse( c.f.cache_info.last_cached )
        
        # test versioning
        
        @version("F")
        def F(x):
            return x
        
        @sub.cache("G")
        def G(x):
            return x
        
        @sub.cache("H", dependencies=[F,G])
        def H(x):
            return G(x)*F(x)

        _ = H(2.)
        self.assertEqual( H.cache_info.version, "H { Test2.test_cache.<locals>.F: F, Test2.test_cache.<l 19b17778" )        
        self.assertEqual( H.cache_info.version, H.version.unique_id64 )        

        # decorate live member functions
        
        class AA(object):
            def __init__(self,x):
                self.x = x
            def f(self,y):
                return self.x*y
        
        a = AA(x=1)
        f = sub.cache("0.1", label=lambda y : f"a.f({y})")(a.f)  # <- decorate bound 'f'.
        _ = f(y=2)  
        self.assertFalse( f.cache_info.last_cached )
        self.assertEqual( f.cache_info.version, "0.1" )
        _ = f(y=2)  
        self.assertTrue( f.cache_info.last_cached )
                
        # funcname

        sub = VersionedCacheRoot("?/subdir_cache_test", exclude_arg_types=[A], keep_last_arguments=True)
        
        @sub.cache("0.1", label=lambda new_func_name, func_name, x, y : f"{new_func_name}(): {func_name} {x} {y}", name_of_func_name_arg="new_func_name")
        def f( func_name, x, y ):
            pass
        f("test",1,y=2)
        self.assertEqual( repr(f.cache_info.arguments), "OrderedDict({'func_name': 'test', 'x': '1', 'y': '2'})" )
        
        # this should just work
        @sub.cache("0.1", label=lambda func_name, x : f"{func_name} {x}")
        def f( func_name, x ):
            pass
        with self.assertRaises(RuntimeError):
            f("test",1)        
            
        # cuttinf off
        @sub.cache("0.1", uid=lambda x,y: f"h2({x},{y})_______________________________________________________________________", exclude_args='debug') 
        def h2(x,y,debug=False):
            if debug:
                print(f"h(x={x},y={y})")  
            return x*y
        h2(1,1)
        self.assertEqual( h2.cache_info.filename, "h2(1,1)________________________________ 46a70d67" )

        
if __name__ == '__main__':
    unittest.main()


