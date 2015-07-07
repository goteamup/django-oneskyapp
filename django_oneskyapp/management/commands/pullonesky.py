# -*- coding: utf-8 -*- 

from django.conf import settings
from django.core import management
from django_oneskyapp.utils import OneSkyApiClientException, OneSkyApiClient
import os


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
			
			"""
				PULL
			"""
			# For each OneSky project..
			for locale_path, project_id in settings.ONESKY_PROJECTS:
				
				print "Using locale path: %s" % locale_path
				client.locale_path = locale_path
				
				# Get languages
				status, json_response = client.project_languages(project_id)
				if status != 200:
					raise OneSkyApiClientException("Unable to retrieve project languages for #%s. OneSky API status: %s, OneSky API message: %s" % (project_id, status, json_response.get("meta",{}).get("message","")))
				project_languages = json_response.get("data",[])
				
				# Get files
				file_names = []
				page = 1
				while page:
					status, json_response = client.file_list(project_id,page=page)
					if status != 200:
						raise OneSkyApiClientException("Unable to retrieve file list for #%s. OneSky API status: %s, OneSky API message: %s" % (project_id, status, json_response.get("meta",{}).get("message","")))
					page = json_response.get("meta",{}).get("next_page",None)
					file_names.extend([file.get("file_name") for file in json_response.get("data",[]) if file.get("file_name").endswith(".po")])
				
				# Pull each translated file
				for file_name in file_names:
					for language in project_languages:
						language_code = language.get('custom_locale', None) or language.get('code',None) or 'unknown'
						if use_underscores:
							language_code = language_code.replace('-','_')
						export_file_name = os.path.join(locale_path, language_code, "LC_MESSAGES", file_name)
						if True or language.get("is_ready_to_publish",None):
							status, json_response = client.translation_export(project_id,locale=language.get("code"),source_file_name=file_name,export_file_name=export_file_name)
							if status == 200:
								print "Saving translation file %s for #%s." % (json_response.get("filename","-No filename in OneSky response-"), project_id)
							elif status == 204:
								print OneSkyApiClientException("Unable to download translation file %s for #%s. File has no content. OneSky API status: %s, OneSky API message: %s" % (export_file_name, project_id, status, json_response.get("meta",{}).get("message","")))
							else:
								print OneSkyApiClientException("Something went wrong with downloading translation file %s for #%s. OneSky API status: %s, OneSky API message: %s" % (export_file_name, project_id, status, json_response.get("meta",{}).get("message","")))
						else:
							print OneSkyApiClientException("Unable to save translation file %s for #%s. Mark it as ready to publish." % (export_file_name, project_id))
			
		except OneSkyApiClientException,e:
			print e
			
		pass
