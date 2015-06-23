# -*- coding: utf-8 -*- 

from django.conf import settings
from django.core import management
from django_oneskyapp.utils import OneSkyApiClientException, OneSkyApiClient
import os
import polib


class Command(management.base.BaseCommand):
    
    help = "Updates your .po translation files using makemessages and uploads them to OneSky translation service. Pushes new translation strings from OneSky to your django app and compiles messages."
    
    def run_from_argv(self, argv):
        self._argv = argv
        self.execute()

    def handle(self, *args, **options):
        use_underscores = True
        
        try:
            # Locale path and necessary settings
            locale_path = settings.LOCALE_PATHS[0] if hasattr(settings,"LOCALE_PATHS") and isinstance(settings.LOCALE_PATHS,(list,tuple)) else settings.LOCALE_PATHS if hasattr(settings,"LOCALE_PATHS") else None #os.path.join(settings.BASE_DIR,"locale")
            
            if not locale_path:
                raise OneSkyApiClientException("LOCALE_PATHS not configured properly. Set your path to locale dir in settings.py as string")
            if not hasattr(settings,"ONESKY_API_KEY") or not hasattr(settings,"ONESKY_API_SECRET"):
                raise OneSkyApiClientException("ONESKY_API_KEY or ONESKY_API_SECRET not configured properly. Please include your OneSky key and secret in settings.py as string")
            if not hasattr(settings,"ONESKY_PROJECTS") or not isinstance(settings.ONESKY_PROJECTS,list):
                raise OneSkyApiClientException("ONESKY_PROJECTS not configured properly. Use list of OneSky project ids.")
            
            # Init API client
            client = OneSkyApiClient(api_key=settings.ONESKY_API_KEY, api_secret=settings.ONESKY_API_SECRET, locale_path=locale_path)
            
            for locale_path, project_id in settings.ONESKY_PROJECTS:
                
                client.locale_path = locale_path
                
                # Get files
                file_names = []
                page = 1
                while page:
                    status, json_response = client.file_list(project_id,page=page)
                    if status != 200:
                        raise OneSkyApiClientException("Unable to retrieve file list for #%s. OneSky API status: %s, OneSky API message: %s" % (project_id, status, json_response.get("meta",{}).get("message","")))
                    page = json_response.get("meta",{}).get("next_page",None)
                    file_names.extend([file.get("file_name") for file in json_response.get("data",[]) if file.get("file_name").endswith(".po")])
                
                for file_name in file_names:
                    if isinstance(settings.LANGUAGES,(list,tuple)):
                        
                        # language_codes = [language_item[0] for language_item in settings.LANGUAGES]
                        language_codes = [settings.LANGUAGE_CODE] #just upload the source language
                        
                        if use_underscores:
                            language_codes = [l.replace('-','_') for l in language_codes]
                        
                        for language_code in language_codes:
                            # Push each local file
                            upload_file_name = os.path.join(locale_path,language_code,"LC_MESSAGES",file_name)
                            
                            if os.path.isfile(upload_file_name):
                                # Remove fuzzy translations using polib (src: http://stackoverflow.com/questions/7372414/removing-all-fuzzy-entries-of-a-po-file)
                                po_file = polib.pofile(upload_file_name)
                                for po_entry in po_file.fuzzy_entries():
                                    if po_entry.previous_msgctxt: po_entry.previous_msgctxt = ""
                                    if po_entry.previous_msgid: po_entry.previous_msgid = ""
                                    if po_entry.previous_msgid_plural: po_entry.previous_msgid_plural["0"] = ""
                                    if po_entry.previous_msgid_plural and "1" in po_entry.previous_msgid_plural: po_entry.previous_msgid_plural["1"] = ""
                                    if po_entry.previous_msgid_plural and "2" in po_entry.previous_msgid_plural: po_entry.previous_msgid_plural["2"] = ""
                                    
                                    if po_entry.msgstr: po_entry.msgstr = ""
                                    if po_entry.msgid_plural: po_entry.msgstr_plural["0"] = ""
                                    if po_entry.msgid_plural and "1" in po_entry.msgstr_plural: po_entry.msgstr_plural["1"] = ""
                                    if po_entry.msgid_plural and "2" in po_entry.msgstr_plural: po_entry.msgstr_plural["2"] = ""
                                    po_entry.flags.remove("fuzzy")
                                po_file.save()
                                
                                # Upload to OneSky
                                if upload_file_name.endswith(".po"):
                                    print "Uploading file: %s" % upload_file_name
                                    client.file_upload(project_id, upload_file_name, file_format = "GNU_PO", locale = language_code, is_keeping_all_strings=False) # TODO: pass is_keeping_all_strings in command cli call
            
        except OneSkyApiClientException,e:
            print e
            
        pass
