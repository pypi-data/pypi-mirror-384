def main():
    import os
    os.environ['DISABLE_PANDERA_IMPORT_WARNING'] = 'True'
    from ebm.__main__ import main as ebm_main
    ebm_main()




if __name__ == '__main__':
    main()
