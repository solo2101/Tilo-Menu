Tilo Documentation.

Copyright (C) 2010 GnoMenu Team, Helder Fraga, Shaun C. Marolf, Chris Hughes

Written by: Shaun C. Marolf, Helder Fraga

-----------------------
Installing Tilo-Menu:
-----------------------

-----------------
Dependencies:
-----------------

python
python-mate*  	To run on the Mate-Panel
python-numpy 		or numpy in some distros

* Recomends:
mozo			menu editor for mate
mate-conf-editor	Configuration editor


------------
Install:
------------

extract the contents of the tar.gz
cd "path of where you extracted the tar.gz"

sudo make install

(depending on the distribution the "sudo" command my change)

Then go to your Mate-panel , right click, add to panel, and select Tilo


--------------------------
Install directories:
--------------------------

Tilo installs by default in /usr/, where the themes get installed in /usr/share and the python code goes in /usr/lib.
You can change this by using the variables PREFIX and DESTDIR, eg:

sudo make install PREFIX=/etc

this will install Tilo in /etc/

--------------
Uninstall:
--------------

sudo make uninstall


For KDE
Try a manual install by runing the command "-plasmapkg -i src/share/plasma/plasmoids/Tilo.zip" as normal user.


