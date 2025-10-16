#!/usr/bin/jq -f
#
# json variable store post processing with jq example
# this selects all variables with signature databases
#
.variables = [ .variables[] | select(.name == "PK"      or
                                     .name == "KEK"     or
                                     .name == "db"      or
                                     .name == "dbx"     or
                                     .name == "MokList" or
                                     .name == "MokListX") ]
