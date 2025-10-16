mkdir liege_urban
mkdir liege_urban/profiles
mkdir liege_urban/profiles/default
cp -rf  ../profiles/default/workflows* liege_urban/profiles/default/
archgenxml workflows.zargo
manage generated.pot
rm -rf ../i18n
rm -rf ../profiles/default/workflows/
mv -f liege_urban/profiles/default/workflows* ../profiles/default/
rm -rf liege_urban
