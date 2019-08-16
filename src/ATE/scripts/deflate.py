# -*- coding: utf-8 -*-
'''
ATE.scripts.deflate -- compresses file(s)

@author:     Tom Hören
@copyright:  2019 TDK™, All rights reserved.
@license:    GPL V3
@contact:    hoeren@micronas.com
'''

import sys, os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
    
__all__ = []
__version__ = 0.1
__date__ = '2019-08-14'
__updated__ = '2019-08-14'

DEBUG = False
TESTRUN = True
PROFILE = False

if DEBUG or TESTRUN or PROFILE:
    project = str.join(os.path.sep, __file__.split(os.path.sep)[:-3])
    if project not in sys.path:
        sys.path.insert(0, project)
    
from ATE.utils.compression.deflate import deflate, supported_compressions, default_compression

default_extensions = ['.stdf', '.std']

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def get_files(dir_path, extensions, recursive):
    '''
    Given recusive-nes and dir_path, find all files with extensions.
    '''
    retval = []
    if recursive:
        for root, _, files in os.walk(dir_path):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext!='' and ext!='.' and ext in extensions:
                    retval.append(os.path.join(root, file))
    else:
        for file in os.listdir(dir_path):
            _, ext = os.path.splitext(file)
            if ext!='' and ext!='.' and ext in extensions:
                retval.append(os.path.join(dir_path, file))
    return retval

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_author = __import__('__main__').__doc__.split("@")[1].replace("author:", '').strip()
    program_organization = __import__('__main__').__doc__.split("@")[2].replace("copyright:", '').split(',')[0].strip()
    program_license = '''%s

  Created by %s on %s.
  Copyright %s, All rights reserved.

  Licensed under GNU GPL V3
  https://www.gnu.org/licenses/gpl-3.0.en.html

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, program_author, str(__date__), program_organization)

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-r", "--recursive", action="store_true", default=False, help="Recurse further in supplied dir(s) [default: %(default)s]")
        parser.add_argument("-p", "--progress", action="store_true", default=False, help="Disable the progress bar(s) [default:%(default)s]")
        parser.add_argument("-c", "--compression", action='store', default=default_compression, choices=list(supported_compressions), help="The compression method to use. [default: %(default)s]")
        parser.add_argument("-e", "--extension", dest='extensions', action='append', default=default_extensions, help="Extensions to deflate. [default: %(default)s]")
        parser.add_argument("-s", "--summary", action='store_true', default=False, help="Disable the summary at the end. [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument(dest="paths", help="Paths to file(s)/direcctory(s) to process", metavar="path", nargs='+')

        # Process arguments
        args = parser.parse_args()

        recursive = args.recursive
        progress = not args.progress
        compression = args.compression
        extensions = args.extensions
        summary = not args.summary
        paths = args.paths

        if TESTRUN:
            print("-" * 50)
            print("recursive = %s" % recursive)
            print("progress = %s" % progress)
            print("compression = %s" % compression)
            print("extensions = %s" % extensions)
            print("summary = %s" % summary)
            print("paths = %s" % paths)
            print("-" * 50)

        # split (and clecleanup) the supplied paths.
        good_dir_paths = []
        good_file_paths = []
        bad_paths = []
        cwd = os.getcwd()
        for path in paths:
            if path.startswith('.'):
                tmp = os.path.normpath(os.path.join(cwd, path))
            else:
                tmp = os.path.normpath(path)
            
            if not os.path.exists(tmp):
                bad_paths.append(tmp)
            elif os.path.isfile(tmp):
                base_path, name = os.path.split(tmp)
                base_name, ext = os.path.split(name)
                if ext!='' and ext!='.' and ext in extensions:
                    good_file_paths.append(tmp)
                else:
                    bad_paths.append(tmp)
            elif os.path.isdir(tmp):
                good_dir_paths.append(tmp)
            else:
                bad_paths.append(tmp)
        # expand the directories giving the supplied recursion
        for dir_path in good_dir_paths:
            good_file_paths += get_files(dir_path, extensions, recursive)
        # remove doubles from good_file_paths
        good_file_paths = list(set(good_file_paths))
        # book keeping
        files_to_process = len(good_file_paths)
        # do the work
        deflate(good_file_paths, compression=compression, progress=progress)
            
        if TESTRUN:
            print("-" * 50)
            print("good_dir_paths = %s" % good_dir_paths) # should be empty list
            print("good_file_paths = %s" % good_file_paths)
            print("bad_paths = %s" % bad_paths)
            print("-" * 50)
        
        
        ### do something with inpath ###

        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
        sys.argv.append("-v")
        sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'ATE.scripts.deflate_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())