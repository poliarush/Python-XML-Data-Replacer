import xml.etree.ElementTree as etree
import random, os, re
from datetime import datetime, timedelta
from glob import glob

__author__ = 'Mykhailo Poliarush' #http://poliarush
__version__ = 0.1

class DataGenerator(object):
	def __init__(self, text):
		self.value = None
		self._raw_string = text
		self._generator, self._string_to_replace = tuple(text.split("|")) if text.find("|") != -1 else (None, text)
		
	def _generate_value(self):
		#d|today, tomorrow, today+15, tomorrow+365
		#n|someid-???-???-??? ???
		#s|something-???-???-???		
		
		if self._generator == 'd':
			self.value = self._generate_date(self._string_to_replace)
		elif self._generator == 's':
			self.value = self._generate_string(self._string_to_replace)
		elif self._generator == 'n':
			self.value = self._generate_number(self._string_to_replace)
		else:
			self.value = self._raw_string
		return self.value
		
	def _generate_date(self, text):
		text = text.strip()

		delta_format = {
			"d":"days",
			"m":"minutes",
			"h":"hours",
			"w":"weeks"
		}
		
		time_format = "%Y-%m-%dT%H:%M:%SZ"
		
		#todo: add error handling
		format, operator, offset, offset_type = re.findall(r'^(\w+)([\+\-])?(\d+)?(\w)?$', text)[0]
		if not (format and operator and offset and offset_type):
			format, operator, offset, offset_type = "today", "+", "0", "d"
		time = eval("%s %s timedelta(%s=%s)" 
			% ("datetime.today()", operator, delta_format[offset_type], offset))
		
		#todo: extract format so it can be passed as parameter
		#2011-11-30T08:07:40Z
		return time.strftime(time_format)
		
	def _generate_number(self, text):
		replace = lambda x: str(random.randint(0,9)) if x == "?" else x 
		return "".join(map(replace, text))

	def _generate_string(self, text):
		chars = range(ord('a'),ord('z')) + range(ord('0'),ord('9')) + range(ord('A'),ord('Z'))
		replace = lambda x: chr(random.choice(chars)) if x == "?" else x 
		return "".join(map(replace, text))
		
	def get_generated_value(self):
		return self._generate_value()

#todo: make class working only for 1 file
class Convertor(object):
	def __init__(self, files):
		#todo:load from file or options
		self.ns = {}
		#todo: load file from directory
		self._files = files
		self._load_xmls()
		
	def _load_xmls(self):
		self._xmls = {}
		for file in self._files:
			namespaces = re.findall(r'xmlns:(\w+)="([^\s]+)"\s?', open(file).read())
			for name, value in namespaces:
				self.ns[name] = value
			print self.ns
			self._xmls[file] = etree.parse(file)
		#print self._xmls
	
	def load_rules_from_file(self, file_path):
		self._rules = []
		self._rule_variables = {}
		#todo: need functionality to hold variables
		for line in open(file_path):
			if line.startswith("#") or line.startswith("\n") or line.startswith("\r\n"):
				continue
			elif line.startswith("%"):
				var_name, var_value = re.findall(r"(%.*)=(.*)", line)[0]
				self._rule_variables[var_name] = self._parse_rule_value(var_value)
				continue
			splitter = "\t"
			self._rules.append(tuple([item.strip() for item in line.strip().split(splitter)]))

	def replace_by_rule(self, rule=None):
		if rule:
			#implement logic to replace rule defined as argument to method
			pass
		else:
			for xml in self._xmls:
				for rule in self._rules:
					elements = self._xmls[xml].findall("."+rule[0], self.ns)
					for element in elements:
						#todo: parse generated values
						if rule[1] in self._rule_variables.keys():
							replaced_rule = self._rule_variables[rule[1]]
						else:
							replaced_rule = rule[1]
						element.text = self._parse_rule_value(replaced_rule)

	def _parse_rule_value(self, rule_value):
		return DataGenerator(rule_value).get_generated_value()
	
	def store(self, folder="output"):
		if not os.path.exists(folder):
			os.mkdir(folder)
			
		for filename in self._xmls:
			#fix input and output variables
			self._xmls[filename].write(
				os.path.join(folder,filename).replace("input", "output"), 
				xml_declaration=True)

def get_files_from_directory(directory, pattern="*.*"):
	abs_path = lambda f: os.path.join(os.path.abspath(os.curdir),f)
	old_dir = os.curdir
	os.chdir(directory)
	files = map(abs_path, glob(pattern))
	os.chdir("..")
	return files

if __name__ == '__main__':
	files = get_files_from_directory("input")
	if not files:
		print "no files found for transformation"
		sys.exit(1)
	
	for file in files:
		convertor = Convertor([file])
		convertor.load_rules_from_file("rules.txt")
		convertor.replace_by_rule()
		convertor.store()