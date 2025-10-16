#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

SQL_9_HEADER = [
    'DROP TABLE IF EXISTS ptadresses_vdl;',
    'SET statement_timeout = 0;',
    'SET client_encoding = \'UTF8\';',
    'SET standard_conforming_strings = on;',
    'SET check_function_bodies = false;',
    'SET client_min_messages = warning;',
    'SET search_path = public, public;',
    'SET default_tablespace = \'\';',
    'SET default_with_oids = false;'
]

SQL_9_FOOTER = [
    'GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE ptadresses_vdl TO {db_owner};',
    'GRANT SELECT ON TABLE ptadresses_vdl TO {db_owner};',
]


def convert_to_psql_9(filename, db_name, db_owner):
    original_dump = open(filename, 'r')
    original_lines = original_dump.readlines()
    new_dump = SQL_9_HEADER
    COPY = False
    for line in original_lines:
        newline = line.rstrip('\n')
        if line.startswith('CREATE') or line.startswith('ALTER TABLE') or line.startswith('COPY'):
            COPY = True
            newline = newline.replace('prod_data.', '')
            newline = newline.replace('managerprod', db_owner)
        if line.startswith('COMMENT') or line.startswith('GRANT'):
            COPY = False
        if COPY:
            new_dump.append(newline)
    for line in SQL_9_FOOTER:
        new_dump.append(line.format(db_owner=db_owner))
    for line in new_dump:
        sys.stdout.write(line+'\n')


req_version = (2, 7)
cur_version = sys.version_info

if cur_version >= req_version:
    import argparse

    def parseArguments():
        parser = argparse.ArgumentParser(description='convert liege ptadresses psql 10 dump to psql 9')
        parser.add_argument('-f', '--filename')
        parser.add_argument('-d', '--db_name')
        parser.add_argument('-U', '--db_owner')
        return parser.parse_args()

    def main():
        arguments = parseArguments()
        arguments = vars(arguments)
        convert_to_psql_9(**arguments)

    if __name__ == "__main__":
        main()
