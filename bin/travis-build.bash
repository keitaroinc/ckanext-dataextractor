#!/bin/bash
set -e

echo "This is travis-build.bash..."

echo "Installing the packages that CKAN requires..."
sudo apt-get update -qq
sudo apt-get install postgresql-$PGVERSION solr-jetty

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/ckan/ckan
cd ckan
export latest_ckan_release_branch=`git branch --all | grep remotes/origin/release-v | sort -r | sed 's/remotes\/origin\///g' | head -n 1`
echo "CKAN branch: $latest_ckan_release_branch"
git checkout $latest_ckan_release_branch
python setup.py develop
pip install -r requirements.txt --allow-all-external
pip install -r dev-requirements.txt --allow-all-external
cd -

echo "Installing ckanext-datasetrelations and its Python dependencies..."
git clone https://github.com/keitaroinc/ckanext-datasetrelations.git
cd ckanext-datasetrelations
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt
cd -

echo "Installing ckanext-edsmetadata and its Python dependencies..."
git clone https://0514b08cc98db32f303114a2550f3114b3ecc61d@github.com/ViderumGlobal/ckanext-edsmetadata.git
cd ckanext-edsmetadata
python setup.py develop
pip install -r dev-requirements.txt
cd -

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c "CREATE USER datastore_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'
sudo -u postgres psql -c 'CREATE DATABASE datastore_test WITH OWNER ckan_default;'

echo "SOLR config..."
# Solr is multicore for tests on ckan master, but it's easier to run tests on
# Travis single-core. See https://github.com/ckan/ckan/issues/2972
sed -i -e 's/solr_url.*/solr_url = http:\/\/127.0.0.1:8983\/solr/' ckan/test-core.ini

# Enable datasetrelations extension
echo "Enabling datasetrelations..."
sed -i -e '/^ckan.plugins/s/$/ datasetrelations/' ckan/test-core.ini

# Enable edsmetadata extension
echo "Enabling edsmetadata..."
sed -i -e '/^ckan.plugins/s/$/ edsmetadata/' ckan/test-core.ini

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
# If Postgres >= 9.0, we don't need to use datastore's legacy mode.
if [ $PGVERSION != '8.4' ]
then
  sed -i -e 's/.*datastore.read_url.*/ckan.datastore.read_url = postgresql:\/\/datastore_default:pass@\/datastore_test/' test-core.ini
  paster datastore -c test-core.ini set-permissions | sudo -u postgres psql
else
  sed -i -e 's/.*datastore.read_url.*//' test-core.ini
fi

cd -

echo "Installing ckanext-dataextractor and its requirements..."
python setup.py develop
pip install -r dev-requirements.txt
pip install -r requirements.txt

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

echo "travis-build.bash is done."