'''
Created on Aug 16, 2019

@author: hoeren
'''

def pprint(plugins, limit_to_languages=False):
    for service  in plugins:
        if service in ['*', 'RCS'] and limit_to_languages:
            continue
        print(service)
        for service_type in plugins[service]:
            print('   %s -> %s' % (service_type, id(plugins[service][service_type])))

def tprint(tree, d=0):
    if (tree == None or len(tree) == 0):
        print("\t" * d, "-")
    else:
        for key, val in tree.items():
            if (isinstance(val, dict)):
                print("\t" * d, key)
                tprint(val, d+1)
            else:
                print("\t" * d, key, str('(') + val + str(')'))

if __name__ == '__main__':
    pass