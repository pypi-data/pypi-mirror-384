# sqltocode-local-python-package
We generate package but we don't use the package. We use it as submodule.

pwsh generate_table_definition.ps1
pwsh /repos/circlez/sql2code-local-python-package/sqltocode_local_python/bin/generate_table_definition.ps1
# Sql2Code

SQL2Code (circles-zone/sql2code-local-python-packge/sql_to_code/src/sqltocode.py running from GHA .github/workflows using sql2code-command-line parameter and calling github-workflows/.github/workflows/???)

SQL2Code is submodule in the repo which is using it. So we can use it from GHA.

# Sql2Code is beeing used in
## database-mysql-local-python-package
https://github.com/circles-zone/database-mysql-local-python-package/blob/dev/.github/workflows/build-publish-database-mysql-local-python-package-play1.yml

## logger-local-python-package

# Sql2Code should be used in many TODOs
python-sdk-local (otherwise real-estate-realtor-com) to create system.py

# Sql2Code should replace existing code: - Low Priority
## database-mysql-local-pythoncreate_table_columns.py 

************ relationship_type_ml_table ************

python3 sqltocode.py --schema relationship_type --table relationship_type_ml_table --language Python --format String  
python3 sqltocode.py --schema relationship_type --table relationship_type_ml_table --columns id,title --language Python --format String  

************ relationship_type_table ************

python3 sqltocode.py --schema relationship_type --table relationship_type_table --language Python --format String  
python3 sqltocode.py --schema relationship_type --table relationship_type_table --columns relationship_type_id,gender_id1 --language Python --format String  

------------------------------------------------------------------------------------------------------



# Versions
[pub] 0.0.27 Write before and afte writing to a file
[pub] 0.0.28 Comment long meanigless logger.info()
