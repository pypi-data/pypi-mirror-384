import os
import argparse
import glob

try:
    from .core import read_compile_write, get_dst_bat, get_dst_workflow
except ImportError:
    from core import read_compile_write, get_dst_bat, get_dst_workflow

def find_pbats(path):
    paths = []
    for n in os.listdir(path):
        if os.path.splitext(n)[1] != '.pbat':
            continue
        p = os.path.join(path, n)
        paths.append(p)
    return paths

def replace_ext(path, ext):
    return os.path.splitext(path)[0] + ext

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs='*', help='file, directory or glob')

    args = parser.parse_args()
    paths = []
    for path in args.path:
        if glob.has_magic(path):
            for path_ in glob.glob(path):
                if os.path.splitext(path_)[1] == '.pbat':
                    paths.append(path_)
        else:
            if os.path.isdir(path):
                paths += find_pbats(path)
            else:
                if os.path.isfile(path):
                    path_ = replace_ext(path, '.pbat')
                    if os.path.isfile(path_):
                        paths.append(path_)
                    else:
                        paths.append(path)
                else:
                    if os.path.splitext(path)[1] == '':
                        path_ = path + '.pbat'
                        if os.path.exists(path_):
                            paths.append(path_)
                        else:
                            print("{} not found".format(path_))
                    else:
                        print("{} not found".format(path))

    if len(args.path) == 0:
        paths = find_pbats('.')

    """
    if len(paths) > 1 and args.output is not None:
        print("--output argument requires one input")
        exit(1)
    """

    for src in paths:
        if False:
            pass
        else:
            dst_bat = get_dst_bat(src)
            dst_workflow = get_dst_workflow(src)
        if src == dst_bat:
            print("src == dst", src)
            exit(1)

        try:
            #print(src, dst_bat, dst_workflow)
            read_compile_write(src, dst_bat, dst_workflow)
        except Exception as e:
            if os.environ.get('DEBUG_PBAT') == '1':
                raise e
            else:
                print(e)

if __name__ == "__main__":
    main()
    