This command is used to save a PowerBI data model from SSAS to a pbix file.
```xml
<ImageSave
	xmlns="http://schemas.microsoft.com/analysisservices/2003/engine"
	xmlns:ddl100="http://schemas.microsoft.com/analysisservices/2008/engine/100"
	xmlns:ddl200="http://schemas.microsoft.com/analysisservices/2010/engine/200"
	xmlns:ddl700_700="http://schemas.microsoft.com/analysisservices/2018/engine/700/700"
>
	<ddl700_700:PackagePath>{{target_path}}</ddl700_700:PackagePath>
	<ddl700_700:PackagePartUri>/DataModel</ddl700_700:PackagePartUri>
	<Object>
		<DatabaseID>{{db_name}}</DatabaseID>
	</Object>
</ImageSave>
```