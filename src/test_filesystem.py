import unittest


class TestVirtualFileSystem(unittest.TestCase):

    def setUp(self):
        
    def test_1(self):
        main_dir = VirtualDir('')
        main_file = main_dir.add_file(
            'main.py', 
            """
                def f():
                    pass
            """
        )
        
        for x in main_dir.iter_sub_dirs():
            pass
            
        for x in main_dir.iter_files():
            pass
            
        buf = main_file.read()
        dt = main_file.mtime
        s = main_file.size
        
        
    def test_update_dir(self):
        old_dir = ...
        mew_dir = ...
        dir_cmp = DirComparer(old_dir, new_dir)
        for x in dir_cmp.iter_new_dirs():
            pass
        for x in dir_cmp.iter_removed_dirs():
            pass
        for x in dir_cmp.iter_common_dirs():
            pass
        for x in dir_cmp.iter_changed_files():
            pass

        
    
      
        
        
        
        
        
        
        
root_dir = NormalDir(root_dpath)

for sub_dir in root_dir.iter_dirs()    
    
if __name__ == '__main__':
    unittest.main()
