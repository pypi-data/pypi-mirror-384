This command lists all the databases in the SSAS instance. It is useful for checking which databases are available before performing operations like loading or saving a PowerBI model or to identify databases that may need to be deleted.

```xml
<Batch Transaction="false" xmlns="http://schemas.microsoft.com/analysisservices/2003/engine">
  <Discover xmlns="urn:schemas-microsoft-com:xml-analysis">
    <RequestType>DBSCHEMA_CATALOGS</RequestType>
    <Restrictions />
    <Properties />
  </Discover>
</Batch>
```