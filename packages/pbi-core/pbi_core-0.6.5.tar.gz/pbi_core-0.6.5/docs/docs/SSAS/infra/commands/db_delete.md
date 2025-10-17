The command to delete a database in SSAS. 

!!! Tip

    By default, PowerBI desktop uses a temporary database for each `.pbix` file. By contrast, `pbi_core` tries to use a persistent database for each project. Because of this, you may need to delete the database to avoid wasting old databases. `pbi_core` will try to automatically delete the database on exit, but you can also delete it manually using this command.

```xml
<Delete xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
  <Object> 
    <DatabaseID>{{db_name}}</DatabaseID>
  </Object>
</Delete>
```