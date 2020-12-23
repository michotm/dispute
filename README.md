# Dipute addons for Odoo

## Available modules
Repos used outside of the mono repos

## Config postgres
Set odoo user as superuser
```
cd ../1001pharmacies/infra
make connect SERVICE=postgres
su - postgres
psql -U odoo -d template1
ALTER USER username WITH SUPERUSER;
\q
############################
# IF odoo user doesn't exist
############################
avec le user postgres
createuser -s odoo -P
# password odoo
```

## Launch Odoo
```
make up
```

## Connect to Odoo
http://localhost:8069

## Create/reset a demo DB
```
scripts/reset_demo_db.sh
```



## Akretion Docky instruction

### Run the container in interactif mode

```
docky run
```

### Setup dev

Inside the container install dependency (this will download odoo and install pip package in the shared volume mounted on the host)

```
install_dev
```

### Install new dependency

If you need to install specific fork version of odoo module or none oca module
add them in requirements.txt.in and then run inside the container

- pip install -r /odoo/requirements.txt.in
- freeze

The file requirements.txt is now updated check it and commit it
