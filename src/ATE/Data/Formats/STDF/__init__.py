import os

from ATE.Data.Formats.STDF.utils import stdfopen as open


project_root = str.join(os.path.sep, os.path.split(__file__)[0].split(os.path.sep)[:-5]) 
resources_path = os.path.join(project_root, 'resources')
samples = os.path.join(resources_path, 'stdf')

def get_stdf_resources(path, recursive=True):
    stdf_files = []
    stdf_gz_files = []
    stdf_bz2_files = []
    stdf_xz_files = []
    
    if not os.path.exists(path):
        return stdf_files, stdf_gz_files, stdf_bz2_files, stdf_xz_files
    
    if not os.path.isdir(path):
        return stdf_files, stdf_gz_files, stdf_bz2_files, stdf_xz_files
    
    if recursive:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('std') or file.endswith('stdf'):
                    stdf_files.append(os.path.join(root, file))
                if file.endswith('std.gz') or file.endswith('stdf.gz'):
                    stdf_gz_files.append(os.path.join(root, file))
                if file.endswith('std.bz2') or file.endswith('stdf.bz2'):
                    stdf_bz2_files.append(os.path.join(root, file))
                if file.endswith('std.xz') or file.endswith('stdf.xz'):
                    stdf_xz_files.append(os.path.join(root, file))
    else:
        for file in os.listdir(path):
            if file.endswith('std') or file.endswith('stdf'):
                stdf_files.append(os.path.join(root, file))
            if file.endswith('std.gz') or file.endswith('stdf.gz'):
                stdf_gz_files.append(os.path.join(root, file))
            if file.endswith('std.bz2') or file.endswith('stdf.bz2'):
                stdf_bz2_files.append(os.path.join(root, file))
            if file.endswith('std.xz') or file.endswith('stdf.xz'):
                stdf_xz_files.append(os.path.join(root, file))

    return stdf_files, stdf_gz_files, stdf_bz2_files, stdf_xz_files

def get_stdf_files(path, recursive=True):
    return get_stdf_resources(path, recursive)[0]

def get_stdf_gz_files(path, recursive=True):
    return get_stdf_resources(path, recursive)[1]

def get_stdf_bz2_files(path, recursive=True):
    return get_stdf_resources(path, recursive)[2]

def get_stdf_zx_files(path, recursive=True):
    return get_stdf_resources(path, recursive)[3]