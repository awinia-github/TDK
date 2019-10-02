import os

from ATE.Data.Formats.STDF.utils import to_df, is_STDF
from ATE.Data.Formats.STDF.utils import MIR_from_file as get_MIR_from_file
from ATE.Data.Formats.STDF.utils import SDRs_from_file as get_SDRs_from_file
from ATE.Data.Formats.STDF.utils import endian_and_version_from_file

project_root = str.join(os.path.sep, os.path.split(__file__)[0].split(os.path.sep)[:-5]) 
resources_path = os.path.join(project_root, 'resources')
samples = os.path.join(resources_path, 'stdf')

def get_resources(path, recursive=True):
    resources = {'stdf':[], 'stdf.gz':[], 'stdf.bz2':[], 'stdf.xz':[]}
    
    if not os.path.exists(path):
        return resources
    
    if not os.path.isdir(path):
        return resources
    
    if recursive:
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('std') or file.endswith('stdf'):
                    resources['stdf'].append(os.path.join(root, file))
                if file.endswith('std.gz') or file.endswith('stdf.gz'):
                    resources['stdf.gz'].append(os.path.join(root, file))
                if file.endswith('std.bz2') or file.endswith('stdf.bz2'):
                    resources['stdf.bz2'].append(os.path.join(root, file))
                if file.endswith('std.xz') or file.endswith('stdf.xz'):
                    resources['stdf.xz'].append(os.path.join(root, file))
    else:
        for file in os.listdir(path):
            if file.endswith('std') or file.endswith('stdf'):
                resources['stdf'].append(os.path.join(root, file))
            if file.endswith('std.gz') or file.endswith('stdf.gz'):
                resources['stdf.gz'].append(os.path.join(root, file))
            if file.endswith('std.bz2') or file.endswith('stdf.bz2'):
                resources['stdf.bz2'].append(os.path.join(root, file))
            if file.endswith('std.xz') or file.endswith('stdf.xz'):
                resources['stdf.xz'].append(os.path.join(root, file))

    return resources

if __name__ == '__main__':
    print(samples)