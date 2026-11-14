#!/usr/bin/env python

# This application is released under the GNU General Public License 
# v3 (or, at your option, any later version). You can find the full 
# text of the license under http://www.gnu.org/licenses/gpl.txt. 
# By using, editing and/or distributing this software you agree to 
# the terms and conditions of this license. 
# Thank you for using free software!
#
#(c) Whise 2009 <helderfraga@gmail.com>
#
# backend for saving and loading settings
# Part of the GnoMenu

import os

try:
        import gconf
        gconf_client = gconf.client_get_default()
        BACKEND = 'gconf'
        print("gconf backend")
except:
        BACKEND = 'xml'
        import xml.dom.minidom
        print("xml backend")

HomeDirectory = os.path.expanduser("~")
ConfigDirectory = HomeDirectory + '/.gnomenu'
gconf_app_key = '/apps/gnomenu'

def save_setting(name,value):

        if BACKEND == 'gconf':
                if isinstance(value, int) or isinstance(value, float):
                        gconf_client.set_int(gconf_app_key + '/' + name , int(value))
                elif isinstance(value, str):
                        gconf_client.set_string(gconf_app_key + '/' + name , str(value))
                elif isinstance(value, list):
                        gconf_client.set_list(gconf_app_key + '/' + name ,1, value)

        elif BACKEND == 'xml':
                if name == '': return
                if os.path.isfile(ConfigDirectory + "/.GnoMenu-Settings.xml"):
                        XMLSettings = xml.dom.minidom.parse(ConfigDirectory + "/.GnoMenu-Settings.xml")
                        XBase = XMLSettings.getElementsByTagName('GnoMenu')[0]
                else:
                        XMLSettings = xml.dom.minidom.Document()
                        XBase = XMLSettings.createElement('GnoMenu')

                try:
                        node = XMLSettings.getElementsByTagName('settings')[0]
                except:
                        node = XMLSettings.createElement('settings')
                node.setAttribute(name, str(value))
                XBase.appendChild(node)
                XMLSettings.appendChild(XBase)
                file = open(ConfigDirectory + "/.GnoMenu-Settings.xml","w")
                XMLSettings.writexml(file, "    ", "", "", "UTF-8")
                XMLSettings.unlink()

        else:
                pass



def load_setting(name):
        if BACKEND == 'gconf':
                try:
                        typ =  gconf_client.get_without_default(gconf_app_key + "/" + name).type
                        
                        if typ == 1:
                                return gconf_client.get_string(gconf_app_key + "/" + name)
        
                        elif typ == 2:
                                return gconf_client.get_int(gconf_app_key + "/" + name)
        
                        elif typ == 6:
                                return gconf_client.get_list(gconf_app_key + "/" + name,1)
        
        
        
                        else: 
                                if name == 'favorites': return []
                                return None

                except : 
                        if name == 'favorites': return []
                return None



        elif BACKEND == 'xml':
                if os.path.isfile(ConfigDirectory + "/.GnoMenu-Settings.xml"):
                        XMLSettings = xml.dom.minidom.parse(ConfigDirectory + "/.GnoMenu-Settings.xml")
                        #print XMLSettings.getElementsByTagName('GnoMenu')[0].childNodes[0].localName
                        x = XMLSettings.getElementsByTagName('GnoMenu')[0].getElementsByTagName("settings")[0]
                        try:
                                x = x.attributes[name].value
                                try: 
                                        a = int(x)
                                        
                                except:
                                        if str(x).find('[]') != -1 and name == 'favorites': return []
                                        

                                        if str(x).find(':') != -1:
                                                
                                                x = str(x).replace(" u'","").replace("u'","").replace("[","").replace("]","").replace("'","").replace('&quot;','"')
                                                a = x.split(',')
                                                print(a                         )
                                        else:
                                                a = str(x)
                                        
                                
                                return a


                        except: 
                                if name == 'favorites': return []
                                return None

                else: 
                        return None

        else:
                pass


def get_default_mail_client():

        if BACKEND == 'gconf':
                return gconf_client.get_string("/desktop/gnome/url-handlers/mailto/command")
        elif BACKEND == 'xml':
                return "xdg-open mailto:"
        else:
                pass

def get_default_internet_browser():

        if BACKEND == 'gconf':
                return gconf_client.get_string("/desktop/gnome/url-handlers/http/command")#"/desktop/gnome/applications/browser/exec")
        elif BACKEND == 'xml':
                return "xdg-open http:"
        else:
                pass

