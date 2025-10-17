The XMLA used to create a blank model in SSAS.

```xml
<Batch xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
  <Create AllowOverwrite="true" xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
    <ObjectDefinition>
      <Database xmlns:ddl200_200="http://schemas.microsoft.com/analysisservices/2010/engine/200/200" xmlns:ddl200="http://schemas.microsoft.com/analysisservices/2010/engine/200">
        <ID>{{db_name}}</ID>
        <Name>{{db_name}}</Name>
        <ddl200_200:StorageEngineUsed>TabularMetadata</ddl200_200:StorageEngineUsed>
        <ddl200:CompatibilityLevel>1550</ddl200:CompatibilityLevel>
      </Database>
    </ObjectDefinition>
  </Create>
</Batch>
```