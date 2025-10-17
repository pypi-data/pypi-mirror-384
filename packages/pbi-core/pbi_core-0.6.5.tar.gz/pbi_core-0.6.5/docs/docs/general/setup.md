# Initial Setup

To ensure that the pbi_core library references the correct Power BI dependencies consistently and with minimal required permissions, it includes a script to copy files from the Power BI installation directories to the pbi_core library directory. This setup is necessary because Power BI does not provide a public API for accessing these files, and the library needs to reference them directly. Additionally, in some local installations, the Power BI installation directory may require administrative permissions to access.

To setup, run the following command:

```shell
run `python -m pbi_core setup`
```    

If the setup cannot find a file, you can generally find the folder by typing "PowerBI" into the startup menu, then open in file folder, and then following the shortcut link.