import sqlite3

def get_input_paths(filename, databases, file_version=None):
    """
    This is a function to resolve a required input name to a full path to the file.

    Inputs:
    -------
       input_filename : str
          The filename to search for
       databases : list
          A list of databases to search, in order of appearence.

    Returns:
    --------
       input_file_path : str
          The full path to the relvant file

    In this particular case, we are going to interact with an sqlite database, building on what
    existed in CCCma. However, this could be done in other ways, with a search, with a csv or
    json database, etc. The existing datapath / access model needs to be reviewed.
    Note that where multiple files exist with the same name, but different versions, only the one
    with the highest version number is returned. The concept of file versions separate from filenames
    is an odd one, but is a legacy at CCCma.
    """
    # Search for filename in databases
    for database in databases:
        con = sqlite3.connect(database)
        cur = con.cursor()
        if file_version:
            con.execute("SELECT fullpath FROM datapath WHERE filename = :file AND ver = :ver", {"file": filename, "ver": file_version})
        else:
            file_version=".*"
            cur.execute("SELECT fullpath FROM datapath WHERE filename = :file ORDER BY ver DESC LIMIT 1", {"file": filename})
        result = cur.fetchall()
        con.close()
        # We found the result so stop searching
        if result:
            break
    # We have searched all provided databases and not found a result
    if not result:
        raise ValueError(f"No file found in {databases} matching filename: {filename} and version {file_version}")
    return result[0][0]
