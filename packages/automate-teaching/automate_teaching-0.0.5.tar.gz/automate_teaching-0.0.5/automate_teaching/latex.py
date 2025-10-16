import os,subprocess, shutil

def is_command_available(command):
    """Checks if a command is available in the system's PATH.

    Args:
        command (str): The command to check.

    Returns:
        bool: True if the command is available, False otherwise.
    """
    return shutil.which(command) is not None


def make_figure(image_filename,position='h',caption=None,label='',hspace='0cm',height='6.5cm',width=None,caption_top=True,center_image=True,filename=None):
    
    """Constructs a LaTeX figure environment.

    Args:
        image_filename (str): Path and filename of the image file.
        position (str): Position specifier for the figure ('h', 't', 'b', 'p'). Default is 'h'.
        caption (str, optional): Caption for the figure. Default is None.
        label (str): Label for referencing the figure. Default is ''.
        hspace (str): Horizontal position offset of the image. Default is '0cm'.
        height (str): Height of the image. Default is '6.5cm'.
        width (str, optional): Width of the image. Default is None.
        caption_top (bool): Whether to place the caption above the figure. Default is True.
        center_image (bool): Whether to center the image in the figure environment. Default is True.
        filename (str, optional): Path to save the generated LaTeX figure file. Default is None.

    Returns:
        str: LaTeX string for the figure environment.
    """
    
    figure = '\\begin{figure}[h]\n'
    
    if caption is not None and caption_top:
        figure+='\\caption{\\label{'+label+'} '+caption+'}\n'
        
    if center_image:
        figure+='\\begin{center}\n'
        
    figure+='\\hspace*{'+hspace+'}\\includegraphics['
    if height is not None:
        figure+='height = '+height
    if width is not None and height is not None:
        figure+=','
    if width is not None:
        figure+='width = '+width


    figure+=']{'+image_filename+'}\n'

    if caption is not None and not caption_top:
        figure+='\\caption{'+caption+'}\n'
    if center_image:
        figure+='\\end{center}\n'
    figure+='\\end{figure}'
    
    if filename is not None:
        try:
            with open(filename,'w') as nf:
                nf.write(figure)
        except:
            print('Invalid path')
    
    return figure

def make_tabular(data,table_spec='',row_format={},column_format={},hlines=[],clines={},pos='c',filename=None):
    
    """Constructs a LaTeX tabular environment.

    Args:
        data (numpy.ndarray): 2D array with data for the table.
        table_spec (str): Column alignment string for the tabular environment. Default is ''.
        row_format (dict): Row-specific formatting, with keys as row number (start from 1) and values are LaTeX formatting commands excluding "\" symbol.
                            Example:
                                        
                            row_format = {1:['textbf','textit']}
                                        
                            will boldface and italicize the first row of the table. Default is {}.
        column_format (dict): Column-specific formatting, with keys as row number (start from 1) and values are LaTeX formatting commands excluding "\" symbol.
                            Example:
                                        
                            column_format = {1:['textbf','textit']}
                                        
                            will boldface and italicize the first column of the table. Default is {}.
        hlines (list): List of row numbers for which horizontal lines will be added below. 0 indicates a line above the first row. Default is [].
        clines (dict): Dictionary with row numbers (starting from 1) as keys and column range strings for clines as values. Example:
                                        
                            clines = {2:['1-3','5-6']}
                                        
                            will add a cline below the 1st through 3rd columns and the 5th and 6th columns of the 2rd row. Default is {}.
        pos (str): Vertical positioning specifier ('b', 'c', 't') of the table relative to text. Default is 'c'.
        filename (str, optional): Path to save the LaTeX tabular file. Default is None.

    Returns:
        str: LaTeX string for the tabular environment.
    """
    
    # First row of the table
    tabular = '\\begin{tabular}['+pos+']{'+table_spec+'}'
    
    # Add top line if necessary
    if 0 in hlines:
        tabular+='\\hline'
        
    tabular +='\n'

    def shift_keys_down_one(dictionary):
        """Decrements all keys in a dictionary by 1.

    Args:
        dictionary (dict): A dictionary with integer keys.

    Returns:
        dict: A new dictionary with all keys decremented by 1.
    """

        return { int(key)-1 : value for key, value in dictionary.items() }

    row_format=shift_keys_down_one(row_format)
    column_format=shift_keys_down_one(column_format)
    clines=shift_keys_down_one(clines)
    hline = hlines = [int(h)-1 for h in hlines]
    
    
    # Iterate over rows of data and add to table
    for row_number,row in enumerate(data):
        
        # Convert row elements to strings
        row = [str(r) for r in row]
        
        # Format columns appropriately
        for column_numbers in column_format.keys():

            column_commands = ''.join(['\\'+f+'{' for f in column_format[column_numbers]])

            row[column_numbers] = column_commands+row[column_numbers]+'}'*len(column_format[column_numbers])
        
        # Add row to table and make 
        if row_number in row_format.keys():
            
            row_commands = ''.join(['\\'+f+'{' for f in row_format[row_number]])
            
            row = [row_commands+r+'}'*len(row_format[row_number]) for r in row]
            
        
        tabular+=' & '.join(row)+'\\\\'
        
        if row_number in hlines:
            tabular+='\\hline'
            
        if row_number in clines.keys():
            for fmt_string in clines[row_number]:

                tabular+='\\cline{'+str(fmt_string)+'}'
        
        tabular+='\n'
    
    tabular+=('\\end{tabular}')
    
    return tabular

def make_table(data,table_spec='',row_format={},column_format={},hlines=[],clines={},position='h',caption=None,label='',caption_top=True,center_table=True,filename=None):
    
    """Constructs a LaTeX table environment with a tabular content.

    Args:
        data (numpy.ndarray): 2D array with data for the table.
        table_spec (str): Column alignment string for the tabular environment. Default is ''.
        row_format (dict): Row-specific formatting, with keys as row number (start from 1) and values are LaTeX formatting commands excluding "\" symbol.
                            Example:
                                        
                            row_format = {1:['textbf','textit']}
                                        
                            will boldface and italicize the first row of the table. Default is {}.
        column_format (dict): Column-specific formatting, with keys as row number (start from 1) and values are LaTeX formatting commands excluding "\" symbol.
                            Example:
                                        
                            column_format = {1:['textbf','textit']}
                                        
                            will boldface and italicize the first column of the table. Default is {}.
        hlines (list): List of row numbers for which horizontal lines will be added below. 0 indicates a line above the first row. Default is [].
        clines (dict): Dictionary with row numbers (starting from 1) as keys and column range strings for clines as values. Example:
                                        
                            clines = {2:['1-3','5-6']}
                                        
                            will add a cline below the 1st through 3rd columns and the 5th and 6th columns of the 2rd row. Default is {}.
        position (str): Position specifier for the table ('h', 't', 'b', 'p'). Default is 'h'.
        caption (str, optional): Caption for the table. Default is None.
        label (str): Label for referencing the table. Default is ''.
        caption_top (bool): Whether to place the caption above the table. Default is True.
        center_table (bool): Whether to center the table in the environment. Default is True.
        filename (str, optional): Path to save the LaTeX table file. Default is None.

    Returns:
        str: LaTeX string for the table environment.
    """
    
    tabular = make_tabular(data,table_spec=table_spec,row_format=row_format,column_format=column_format,hlines=hlines,clines=clines)
    
    
    table = '\\begin{table}['+position+']\n'
    
    if caption is not None and caption_top:
        table+='\\caption{\\label{'+label+'} '+caption+'}\n'
        
    if center_table:
        table+='\\begin{center}\n'
    table+=tabular+'\n'
    if caption is not None and not caption_top:
        table+='\\caption{'+caption+'}\n'
    if center_table:
        table+='\\end{center}\n'
    table+='\\end{table}'
    
    if filename is not None:
        try:
            with open(filename,'w') as nf:
                nf.write(table)
        except:
            print('Invalid path')
    
    return table
    
def DataFrame_to_array(df,include_index=True,include_column_headers=True,keep_index_name=True):
    
    """Converts a Pandas DataFrame to a NumPy array, including row and column headers.

    Args:
        df (pandas.DataFrame): Input DataFrame.
        include_index (bool): Whether to include the index in the output. Default is True.
        include_column_headers (bool): Whether to include column headers. Default is True.
        keep_index_name (bool): Whether to keep the index name in the output. Default is True.

    Returns:
        numpy.ndarray: Converted array with headers and index if specified.
    """

    if df.index.name==None or keep_index_name==False:
        df.index.name=''
    

    retval = df.reset_index().T.reset_index().T.to_numpy()

    if not include_index:

        retval = retval[:,1:]

    if not include_column_headers:

        retval = retval[:1]



    # df = df.T.reset_index().T.reset_index()

    # if not keep_index_name:
        # df.loc[df.index[0]].loc[df.loc[df.index[0]].index[0]] = ''
    
    return retval
    


    import os,subprocess

'''Contains programs for the management of lecture notes, slides, tables, and figures'''

def compile(x=None):
    """Compiles LaTeX files in the current directory or specified files.

    Args:
        x (str or list, optional): Filename or list of filenames to compile. If None, compiles all `.tex` files in the current directory.

    Deletes:
        Auxiliary files generated during compilation.

    Raises:
        RuntimeError: If `pdflatex` or `bibtex` is not available in the system.
    """

    if not is_command_available("pdflatex"):
        raise RuntimeError("`pdflatex` is not installed or not found in PATH. Please install MacTeX or ensure `pdflatex` is accessible.")
    if not is_command_available("bibtex"):
        raise RuntimeError("`bibtex` is not installed or not found in PATH. Please install MacTeX or ensure `bibtex` is accessible.")

    os.chdir(os.getcwd())

    if x is None:
        for file in os.listdir('.'):
            if file.endswith('.tex'):
                pdf_latex(file)
    elif isinstance(x, str):
        pdf_latex(x)
    else:
        for file in x:
            pdf_latex(file)

    for file in os.listdir('.'):
        if file.endswith(('.aux', '.log', '.out', '.gz', '.snm', '.nav', '.toc', '.blg', '.bbl', '.vrb')):
            os.remove(file)

def pdf_latex(file_name):
    """Compiles a LaTeX file using `pdflatex`.

    Args:
        file_name (str): Name of the LaTeX file to compile.

    Raises:
        RuntimeError: If `pdflatex` or `bibtex` is not available in the system.
    """

    FNULL = open(os.devnull, 'w')
    pdf_latex_cmd = f'pdflatex "{file_name}"'
    if not file_name.endswith('.tex'):
        pdf_latex_cmd += '.tex'

    bibtex_cmd = pdf_latex_cmd.replace('.tex', '.aux').replace('pdflatex', 'bibtex')

    try:
        subprocess.call(pdf_latex_cmd, shell=True, stdout=FNULL)
        subprocess.call(pdf_latex_cmd, shell=True, stdout=FNULL)
        subprocess.call(bibtex_cmd, shell=True, stdout=FNULL)
        subprocess.call(bibtex_cmd, shell=True, stdout=FNULL)
        subprocess.call(pdf_latex_cmd, shell=True, stdout=FNULL)
        subprocess.call(pdf_latex_cmd, shell=True, stdout=FNULL)
    except Exception as e:
        raise RuntimeError(f"An error occurred while running `pdflatex` or `bibtex`: {e}")
    

def make_handout(slides_file_name,handout_file_name):
    """Generates a LaTeX handout file for Beamer slides (i.e. the handout option is included to document preamble.

    Args:
        slides_file_name (str): Name of the original slides file.
        handout_file_name (str): Name of the generated handout file.
    """
    '''For Beamer lecture slides named file_name, a new file is created the preamble is modified to inclue the handout option.'''

    if not slides_file_name.endswith('.tex'):

        slides_file_name+='.tex'

    if not handout_file_name.endswith('.tex'):

        handout_file_name+='.tex'

    with open(slides_file_name) as oldLines, open(handout_file_name, "w") as newLines:
        for n,line in enumerate(oldLines):
            if n==0:
                newLines.write(line[0:15]+'handout,'+line[15:])
            else:
                newLines.write(line)

# def create_handouts(slideList):
#     '''Returns a list of handout file names for each file name in slideList'''

#     handout_list=[]
#     for s in slideList:
#         handout_list.append('Handout'+s[6:])
#         handout(s)
#     return handout_list

def python_script(script):
    """Executes a Python script or list of scripts.

    Args:
        script (str or list): Filename or list of filenames for Python scripts.
    """

    if type(script)==str:
        if script.endswith('.py')==False:
            script = script+".py"
        run = subprocess.call("python "+script, shell=True)
    else:
        for s in script:
            if s.endswith('.py')==False:
                s = s+".py"
            run = subprocess.call("python "+s, shell=True)