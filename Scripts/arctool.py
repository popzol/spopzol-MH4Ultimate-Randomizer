#!/usr/bin/python
# Copyright 2016 dasding
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import argparse

from lib.util import *
from lib.arc import ARC


def extract(filename, args):
    index = args.index
    base_path = args.base_path
    base_path = base_path + os.path.sep
    arc = ARC(readFile(filename))
    log_info(arc)

    if not os.path.exists(base_path):
        os.makedirs(base_path)

    if index:
        arc_index_path = index
    else:
        arc_index_path = base_path + 'arc_index'
    index_file = open(arc_index_path, 'wb')

    for f in arc.file_list:
        directory = base_path + os.path.dirname(f['file'])
        if not os.path.exists(directory):
            os.makedirs(directory)

        writeFile(base_path + f['file'], f['data'])
        index_file.write('{}\t{}\n'.format(f['file'], f['raw_ext']))

    index_file.close()


def create(filename, args):
    base_path = args.base_path
    index = args.index

    if index:
        arc_index_path = index
    else:
        arc_index_path = args.base_path + os.path.sep + 'arc_index'

    if os.path.exists(arc_index_path):
        file_list = str(readFile(arc_index_path))
        file_list = file_list.split('\n')[:-1]
        file_list = [args.base_path + os.path.sep + file for file in file_list]
    else:
        file_list = list_files(base_path)

    arc = ARC()
    if args.ver:
        arc.version = int(args.ver)
    log_info(arc)

    for file in file_list:
        file = file.split('\t')
        f = os.path.relpath(file[0], start=base_path)
        arc.add_file(f, readFile(file[0]), file[1])

    writeFile(filename, arc.export_arc())


def display(filename):
    arc = ARC()
    f = readFile(filename)
    arc.parse_header(f)
    arc.parse_file_list(f)

    print(arc)
    print('filelist:')
    print("{:>8} {:>8} {:>4} {}".format('c_size', 'u_size', 'unk', 'filename'))
    for f in arc.file_list:
        print("{size:8} {unc_size:8} {unk0:3} {offset:8} {file}".format(**f))


def list_files(base_path):
    entries = os.listdir(base_path)
    file_list = []

    for entry in entries:
        path = os.path.join(base_path, entry)
        if os.path.isdir(path):
            file_list += list_files(path)
        else:
            file_list.append(path)
    return file_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract and create MT Mobile Framework .arc files")
    group = parser.add_mutually_exclusive_group()

    group.add_argument("-x", "--extract", action="store_true", help="extract an archive")
    group.add_argument("-c", "--create", action="store_true", help="create an archive")
    group.add_argument("-l", "--list", action="store_true", help="list all files in an archive")

    parser.add_argument("-i", "--index", action="store", help="specify an arc_index to use")
    parser.add_argument("-v", "--verbose", action="count", help="increase output verbosity")
    parser.add_argument("-vr", "--ver", action="store", help="use a specific version")
    parser.add_argument("base_path", help="Base path for extracted files")
    parser.add_argument("input", nargs="+", help=".arc file to extract/create")

    args = parser.parse_args()

    enable_log(args.verbose)

    for filename in args.input:
        if args.extract:
            extract(filename, args)
        elif args.create:
            create(filename, args)
        else:
            display(filename)