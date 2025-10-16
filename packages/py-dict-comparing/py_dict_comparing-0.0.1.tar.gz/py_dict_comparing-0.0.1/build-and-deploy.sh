BASEDIR=$(dirname $0)
pushd $BASEDIR
./build.sh
twine upload dist/* -u $TWINE_USERNAME -p $TWINE_PASSWORD
popd
