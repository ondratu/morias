#!/bin/sh

langs="cs"
program=morias

#printf " xgettext \t${program}\t...\n"
#xgettext -o ${program}.pot    --language=python --keyword=_ --from-code utf-8 --escape ../templ/*.html
#xgettext -o ${program}.pot -j --language=python --keyword=_ --from-code utf-8 --escape ../templ/*/*.html

printf " pybabel extract \t"
pybabel extract -F babel.cfg -k lazy_gettext -o ${program}.pot .. 2>&1 | while read x; do printf "."; done
printf " Done\n"

for lang in $langs; do
    printf " msgmerge \t$lang\t"
    mv ${lang}.po ${lang}.po.bak
    msgmerge ${lang}.po.bak ${program}.pot > ${lang}.po;

    printf " msgfmt \t$lang\t"
    mkdir -p ${lang}/LC_MESSAGES
    msgfmt -o ${lang}/LC_MESSAGES/${program}.mo ${lang}.po && printf "Done\n" || printf "Failed\n"
done;
