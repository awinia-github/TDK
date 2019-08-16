supported_compressions = {'lzma' : '.xz', 'gzip' : '.gz', 'bz2' : '.bz2'}
supported_compressions_extensions = {supported_compressions[k]:k for k in supported_compressions}
default_compression = 'lzma'

if default_compression not in supported_compressions:
    raise KeyError("%s not in %s" % (default_compression, supported_compressions))