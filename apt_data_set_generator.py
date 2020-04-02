#!/usr/bin/python
# apt_data_set_generator.py - generate the apt_data_set.py file

#-------------------------------------------------------------------------------

def generate_code(py_filename, class_name, params):
    # Class header
    s = f"""#!/usr/bin/python
# {py_filename}.py - one Debian package description 

#-------------------------------------------------------------------------------
# {class_name} - 
#-------------------------------------------------------------------------------

class {class_name}():
    \"\""Represents one paragraph in a debian control file (such as Packages).

    Reference is https://www.debian.org/doc/debian-policy/ch-controlfields.html
\"\""
"""
    #---------------------------------------------------------------------------
    # __init__ function parameters
    #---------------------------------------------------------------------------

    t = '    def __init__('
    n = len(t)
    t += 'self,'
    iparams = iter(params)
    try:
        while True:
            # Fill in lines of parameters in the source code text
            while True:
                # Add parameters to the current line
                p = next(iparams)
                t2 = f'{t} {p}=None,'
                if len(t2) > 80:
                    break
                t = t2
            s += t + '\n'
            t = ' '*n + f'{p}=None,'
    except StopIteration:
        s += f'{t[:-1]}):\n'

    #---------------------------------------------------------------------------
    # __init__ function body
    #---------------------------------------------------------------------------

    for p in params:
        s += ' '*8 + f'self.{p} = {p}\n'
    s += '\n'

    #---------------------------------------------------------------------------
    # __str__ function
    #---------------------------------------------------------------------------

    s += """    def __str__(self):
        s = ''
"""
    for p in params:
        s += f"        s += f'{p}: {{self.{p}}}\\n'\n"
    s += '        return s\n'
    s += '\n'

    #---------------------------------------------------------------------------
    # to_csv function
    #---------------------------------------------------------------------------

    s += """    def to_csv(self):
        s = ''
"""
    for p in params:
        s += f"        s += f'{{self.{p}}}\\t'\n"
    # Remove the last '\t'
    s = s[:-4] + "'\n"
    s += '        return s\n'
    s += '\n'

    #---------------------------------------------------------------------------
    # csv_header function
    #---------------------------------------------------------------------------

    s += """    @classmethod
    def csv_header(self):
        s = ''
"""
    for p in params:
        s += f"        s += '{p}\\t'\n"
    # Remove the last '\t'
    s = s[:-4] + "'\n"
    s += '        return s\n'
    s += '\n'

    #---------------------------------------------------------------------------
    # to_csv class method
    #---------------------------------------------------------------------------
    
    s += f"""    @classmethod
    def to_csv(self, filepath):
        with open(filepath, 'w') as f:
            f.write({class_name}.csv_header() + '\\n')
            for ds in self.data_sets:
                f.write(ds.to_csv() + '\\n')
"""
    return s

#===============================================================================
# main
#===============================================================================

with open('apt_data_set_params.txt', 'r') as f:
    params = f.read().split()

py_filename = 'apt_data_set'
s = generate_code(py_filename, 'DataSet', params)
with open(f'{py_filename}.py', 'w') as f:
    f.write(s)
