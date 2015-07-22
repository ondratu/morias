#!/bin/bash

db=$1
if [ "x$db" == "x" ]; then
    printf "Usagge: $0 database.db\n"
    exit 1
fi;

ver=`sqlite3 -version`
if [ $? != 0 ]; then
    printf "Do not have sqlite3\n"
    exit 1
fi;

dir=`dirname $0`

printf "Install module: "

printf "login "
sqlite3 $1 < ${dir}/login.sql
sqlite3 $1 < ${dir}/logins.01.sql

printf "options "
sqlite3 $1 < ${dir}/options.sql

printf "jobs "
sqlite3 $1 < ${dir}/jobs.sql

printf "page_menu "
sqlite3 $1 < ${dir}/page_menu.sql

printf "page_file "
sqlite3 $1 < ${dir}/page_file.sql
sqlite3 $1 < ${dir}/page_files.01.sql

printf "attachments "
sqlite3 $1 < ${dir}/attachments.sql
sqlite3 $1 < ${dir}/attachments.01.sql
${dir}/attachments.01.py $1

printf "news "
sqlite3 $1 < ${dir}/new.sql
sqlite3 $1 < ${dir}/news.01.sql

printf "eshop_store "
sqlite3 $1 < ${dir}/eshop_store.sql

printf "eshop_orders"
sqlite3 $1 < ${dir}/eshop_orders.sql

printf "\nInstalled\n"
