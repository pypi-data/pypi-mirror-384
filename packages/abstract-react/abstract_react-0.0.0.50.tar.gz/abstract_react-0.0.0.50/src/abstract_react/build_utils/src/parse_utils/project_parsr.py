from abstract_utilities import *
def create_dirs(basePath,nuPath):
    full_path = os.path.join(basePath,nuPath)
    if not os.path.exists(full_path):
        full_path = basePath
        pieces = [piece for piece in path.split('/') if piece]
        for piece in pieces:
            full_path = os.path.join(full_path,piece)
            os.makedirs(full_path,exist_ok=True)
    return full_path
def get_content_lines(contents=None,filepath=None):
    if not contents and filepath and os.path.isfile(filepath):
        contents = read_from_file(filepath)
    if contents:
        line_spl=None
        if isinstance(contents,str): 
            line_spl = contents.split('\n')
        if isinstance(contents,list):
            line_spl = contents
        return line_spl
def get_index_content(contents=None,filepath=None):
    line_spl = get_content_lines(contents=contents,filepath=filepath)
    export_ls=[]
    exp_all = False
    filename='.'
    if filepath:
        dirname = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        filename,ext = os.path.splitext(basename)
    for line in line_spl:
        if line.startswith('export'):
            item = eatAll(line.split('(')[0].split('=')[0].split('function')[-1].split('const')[-1].split(' ')[-1],[' ','','\n','\t',';'])
            if 'default ' in line:
                export_ls.append("export {"+f"default as {item}"+"}"+f" from './{filename}';")
            elif exp_all == False:
                exp_all = True
                export_ls.append(f"export * from './{filename}';")
    index_cont = '\n'.join(export_ls)
    return index_cont
def create_script_dir(contents=None,file_path=None,script_dir=None):
    line_spl = get_content_lines(contents=contents,file_path=file_path)
    content_lines = line_spl[1:]
    contents = '\n'.join(content_lines)
    index_cont = get_index_content(contents=content_lines)
    if script_dir:
        dirname = os.path.dirname(file_path)
        basename = os.path.basename(file_path)
        filename,ext = os.path.splitext(basename)
        if script_dir == True:
            script_dir = os.path.join(dirname,filename)
        if not os.path.isdir(script_dir):
            create_dirs(script_dir)
        os.path.join(script_dir,basename)
    index_path = os.path.join(dirbase,'index.ts')
    base_path = os.path.join(dirbase,basename)
    write_to_file(contents=contents,file_path=base_path)
    write_to_file(contents=index_cont,file_path=index_path) 
def create_base_path(path):
    return os.path.join(BASE_DIR,path)
def create_base_dir(path):
    base_path = create_base_path(path)
    if not os.path.exists(base_path):
        base_path = create_dirs(BASE_DIR,path)
    return base_path
src_path = '/var/www/presites/abstractendeavors/react/temp'
go=False
for part in text.split('###')[1:]:
    post_line = part.split('\n')[0]

    go=True
    if go == True:
        post_src = post_line.split('(')[1].split(')')[0].split('`')[1].split('src/')[-1]
        path = os.path.join(src_path,post_src)
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            create_dirs(src_path,post_src)
        basename = os.path.basename(path)
        filename,ext = os.path.splitext(basename)
        dirbase = os.path.join(dirname,filename)
        os.makedirs(dirbase,exist_ok=True)
        index_path = os.path.join(dirbase,'index.ts')
        base_path = os.path.join(dirbase,basename)

        contents = part.split('```')[1]
     
