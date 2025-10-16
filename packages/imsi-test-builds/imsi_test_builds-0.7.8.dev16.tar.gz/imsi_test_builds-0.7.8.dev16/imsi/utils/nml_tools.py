"""
nml_tools
=========

This is a module to collect common namelist functions.

This currently exists because neither f90nml nor the rpn nml tools correctly parse
the nemo namelists. Ideally all these functions would be replaced with more
robust, community packages.

NCS, 10/2021
"""
import os
import re


def nml_update(nml_input_file, nml_output_file, nml_changes):
   """
   An interface function to update namelist parameters.

   Inputs:
      nml_input_file : str
         path to the namelist file to load in
      nml_output_file : str
         path to the updated namelist file to write
      nml_changes : dict
         A nested dict containing. At the top level the keys are the names of the namelists in nml_input_file,
         the values are dicts containing key = value pairs to change in the namelist.

   This is a basic python implementation of the `mod_nl` routine. Ideally the work would be done by a standard
   fortran namelist parser, such as f90nml. However, no existing parsers work correctly on NEMO namelists.
   """
   with open(nml_input_file, 'r') as infile:
      filedata = infile.read()

   # todo - it could be possible to preserve comments after the replacement by using a more
   # sophisticated re, or by doing a split on `!` like in the read function below.
   with open(nml_output_file, 'w') as outfile:
      for line in filedata.split('\n'):
         lineout = line
         for nam, namdict in nml_changes.items():
            for k, v in namdict.items():
               k0 = re.sub(r'(\(|\))',r'\\\1',k)
               lineout = re.sub(rf'^ *{k0} *=.*', f'{k} = {v}', lineout)
         outfile.write(f'{lineout}\n')


def nml_write(nml_output_file, nml):
   """
   An interface function to write namelists from a dict.

   Inputs:
      nml_output_file : str
         path to the namelist file to write
      nml : dict
         A nested dict containing. At the top level the keys are the names of the namelists,
         the values are dicts containing key = value pairs of the namelist.

   Ideally the work would be done by a standard fortran namelist parser, such as f90nml.
   However, no existing parsers work correctly on NEMO namelists.
   """
   with open(nml_output_file, 'w') as outfile:
      for nam, namdict in nml.items():
         outfile.write(f'&{nam}\n')
         for k, v in namdict.items():
            outfile.write(f'{k} = {v}\n')
         outfile.write(f'/\n')

def nml_read(nml_input_file):
   """
   An interface function to read namelists into a dict.

   Inputs:
      nml_input_file : str
         path to the namelist file to read

   Ideally the work would be done by a standard fortran namelist parser, such as f90nml.
   However, no existing parsers work correctly on NEMO namelists.
   """
   with open(nml_input_file, 'r') as infile:
      filedata = infile.read()

   nml = {}
   for line in filedata.split('\n'):
      if line.strip().startswith('&'):
          key = re.sub(r'!.*', '', line).replace('&','').strip()
          nml[key] = {}
          continue
          print(key)
      if line.strip().startswith('/'):
         key = 'ERROR'
         continue
      if line.strip().startswith('!'):
         continue
      if line:
         key_value_comment = line.split('!',1)
         key_value = key_value_comment[0]
         if len(key_value_comment)>1:
            comment = key_value_comment[1]
         else:
            comment = ''
         k = re.sub(r'=.*', '', key_value).strip()
         v = re.sub(r'.*=', '', key_value).strip()
         nml[key][k] = v.strip()
         #print(f'{k} = {v} !{comment}')
   return nml

def cpp_update(cpp_input_file, cpp_output_file, cpp_changes, verbose=False):
    """
    An interface function to update cpp keys.

    Inputs:
       cpp_input_file : str
          path to the cpp file to load in
       cpp_output_file : str
          path to the updated cpp file to write
       cpp_changes : dict
          key = value pairs to change in the file, where
          key appears in the default cpp file, and value is the value to replace it with

    This is a basic python implementation of the `mod_nl` routine. Ideally the work would be done by a standard
    fortran namelist parser, such as f90nml. However, no existing parsers work correctly on NEMO namelists.
    """
    # Note not yet tested on NEMO .fcm files
    with open(cpp_input_file, 'r') as infile:
        filedata = infile.read()

    with open(cpp_output_file, 'w') as outfile:
        for line in filedata.split('\n'):
            lineout = line
            if ('replace' in cpp_changes.keys()):
                for k, v in cpp_changes['replace'].items():
                    if verbose:
                        print(f'in CPP replacing {k} {v}')

                    # likely too general for fcm files, since
                    # multiple keys appear on one line.
                    lineout = re.sub(rf'.*{k}.*', f'{v}', line)

            outfile.write(f'{lineout}\n')
        if ('add' in cpp_changes.keys()):
            for k, v in cpp_changes['add'].items():
                lineout = k
                outfile.write(f'{lineout}\n')

def update_env_file(infile: str, outfile: str = None, updates: dict = None,
                   commment_char: str = '#', key_value_only: bool = True):
   """Update simple shell/environment files.

   Only replaces values of existing keys, i.e. does not add key-value
   pairs that are not already in the file.

   If `key_value_only` is True, then only lines that are in the key=value
   pattern (and commented lines) will be written to the output file.
   To keep all lines, set `key_value_only=False`.
   """
   comment_char = "#"
   linepattern = re.compile(r'(\w+)\s*=\s*(.*)')

   if outfile is None:
      outfile = infile
   if not updates:
      raise ValueError('updates must be a dict with at least one key-value pair')
      # return

   with open(infile, 'r') as f:
      filedata = f.read()

   try:
      with open(outfile, 'w') as out:
            for line in filedata.split('\n'):
               ls = line.strip()
               lineout = line

               if not line or ls.startswith(comment_char):
                  out.write(lineout+'\n')
                  continue

               m = linepattern.search(ls)
               if m:
                  param, val_current = m.groups()
                  if param in updates:
                        val_new = str(updates[param]).strip('"')
                        if val_current:
                           lineout = line.replace(val_current, val_new)
                        else:
                           # handles if the value was left unset (empty after =)
                           lineout = f'{line}{val_new}'

                  out.write(lineout+'\n')

               else:
                  if not key_value_only:
                        # keep the other lines
                        out.write(lineout+'\n')

   except Exception as e:
      if infile != outfile and os.path.exists(outfile):
            os.remove(outfile)
      raise Exception(f'Error writing file {outfile}; no file produced') from e
