import configparser
import smtplib, ssl
import subprocess
import requests
import json
import re
import pandas as pd
import datetime
import time
import boto3
import os
import mimetypes
from requests_ntlm import HttpNtlmAuth
from os.path import abspath
from pyspark.sql import SparkSession
from pyspark.sql import HiveContext
from pyspark.sql.types import *
from pyspark.sql import DataFrame as SparkDataFrame
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dateutil.relativedelta import relativedelta
from datetime import date as dt, timedelta
from urllib.parse import quote
from email.mime.base import MIMEBase
from email import encoders
from xurpas_data_quality import DataReport
from .services.itemreader import ItemReader
from .tools.excelreader import FileReader
from .services.http.main import Xurl
from .services.http.api_reader import APIReader
from .tools.encryption import CipherSuite
from .services.google import XGoogleService as xgservice

debug_mode: bool
job_type: str

def initialize(args):
	#initialize global variables
	global jobArguments
	global customJobArgs
	global targetTableDataset
	global writeDate
	global processDate
	global targetTable
	global targetTableOptions
	global sourceTableOptions
	global jdbcOptions
	global sourceTables
	global sparkConfig
	global sparkDefaultOptions
	global auditOptions
	global startTimestamp
	global optionalParams
	global startTimestamp
	global startTimeEpoch
	global scope_env
	global debug_mode
	global job_type

	jobArguments = {}
	customJobArgs = {}
	targetTableOptions = {}
	sourceTableOptions = {}
	jdbcOptions = {}
	sourceTables = {}
	sparkConfig = {}
	sparkDefaultOptions = {}
	auditOptions = {}
	optionalParams = {}
	startTimestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	startTimeEpoch = time.perf_counter()
	scope_env = "DEV"
	debug_mode = False
	job_type = "default"

	print("--------------------")
	print("-      Job Args    -")
	print("--------------------")
	for i in range(len(args)):
		jobArg = args[i]
		if(i == 0):
			jobArguments["py-file"] = jobArg
		else:
			print(str(i) + " : " + str(jobArg))
			item = jobArg.replace("--", "")
			key = item.split("=")[0]
			value = item.split("=")[1]
			jobArguments[str(key)] = value
			if(item.startswith("customJobArgs")):
				customArg = item.replace("customJobArgs=", "").split("=",2)
				customJobArgs[customArg[0]] = customArg[1]
	
	# checking for new arg from custom
	if "debug" in jobArguments is not None and jobArguments["debug"]:
		debug_mode = True
	if "job_type" in jobArguments:
		job_type = jobArguments["job_type"].strip()

	# setup appName / processDate / writeDate
	global appName
	appName = jobArguments["client-id"] + "." + jobArguments["target-table"]
	processDate = datetime.datetime.strptime(jobArguments["process-date"], "%Y-%m-%d").date()
	writeDate = datetime.datetime.strptime(jobArguments["process-date"], "%Y-%m-%d").date()
	
	#setup properties reader
	global jobProperties
	jobProperties = configparser.ConfigParser()
	jobProperties.read(jobArguments["properties-file"])
	
	#setup global configurations
	x = callAPI(apiURL=getDefaultJobProperties("global.config"), httpMode="get").json()
	jobGlobalConfigurations = x["message"]
	for item in jobGlobalConfigurations["global_parameters"]:
		key = item["key"]
		if(key.startswith("spark.") or key.startswith("session.")):
			if(key.startswith("session.")):
				key = key.replace("session.", "", 1)
			sparkConfig[key] = item["value"]
			if(item["key"].startswith("spark")):
				sparkDefaultOptions[item["key"]] = item["value"]
		elif(item.get("key").startswith("audit")):
			auditOptions[item.get("key").replace("audit.", "")] = item.get("value")
		if(key.startswith("environment")):
			scope_env = item["value"].upper()
	
	#setup target table dictionary
	contextApi = getDefaultJobProperties("job.context") + jobArguments.get("client-id") + "/" + jobArguments.get("target-table").replace(".", "/")
	x = callAPI(apiURL=contextApi, httpMode="get").json()
	jobTables = x["message"]
	targetTable = {}
	
	if("storage_type" in jobTables.keys()):
		storageType = jobTables["storage_type"]
		if("AWS" in storageType.upper()):
			targetTable["storage_type"] = "s3a://"
		elif("GCS" in storageType.upper()):
			targetTable["storage_type"] = "gs://"
		elif("HDFS" in storageType.upper()):
			targetTable["storage_type"] = "hdfs://"
	else:
		targetTable["storage_type"] = "s3a://"

	targetTable["table_name"] = jobTables["table_name"]
	targetTable["database_name"] = jobTables["database_name"]
	if "resource" in jobTables.keys():
		targetTable["resource"] = jobTables["resource"]
	else:
		targetTable["resource"] = ""
	targetTable["folder"] = jobTables["folder"] + "/"
	if "local" in jobArguments["master"]:
		targetTable["path"] = jobTables["folder"]
	else:
		targetTable["path"] = targetTable["storage_type"] + targetTable["resource"] + jobTables["folder"]
	targetTable["write_mode"] = jobTables["write_mode"]
	targetTable["redistribution"] = jobTables["redistribution"]
	targetTable["partition_name"] = jobTables["partition_name"]
	targetTable["partition_date_format"] = jobTables["partition_date_format"]
	targetTable["format"] = jobTables["format"]
	targetTable["number_of_partitions"] = jobTables["number_of_partitions"]

	if("optional_parameters" in jobTables.keys()):
		for param in jobTables["optional_parameters"]:
			key = param.get("key")
			optionalParams[key] = param.get("value")
			if(key == "options.target"):
				targetTableOptions = json.loads(param.get("value"))
			elif(key.startswith("options.target.")):
				key = key.replace("options.target.","")
				targetTableOptions[key] = param.get("value")
			elif(key.startswith("options.jdbc.")):
				key = key.replace("options.jdbc.","")
				jdbcOptions[key] = param.get("value")
			elif(key.startswith("options.source.")):
				key = key.replace("options.source.","")
				sourceTableOptions[key] = json.loads(param.get("value"))
		jdbcOptions["dbtable"] = targetTable["table_name"]

	if("dependencies" in jobTables.keys()):
		for item in jobTables["dependencies"]:
			sjc = item["source_job_context"]
			source = {}
			if("storage_type" in sjc.keys()):
				storageType = sjc["storage_type"]
				if("AWS" in storageType.upper()):
					source["storage_type"] = "s3a://"
				elif("GCS" in storageType.upper()):
					source["storage_type"] = "gs://"
				elif("HDFS" in storageType.upper()):
					source["storage_type"] = "hdfs://"
			else:
				source["storage_type"] = "s3a://"

			tableName = sjc["table_name"]
			source["table_name"] = tableName
			source["database_name"] = sjc["database_name"]
			if "resource" in sjc.keys():
				source["resource"] = sjc["resource"]
			else:
				source["resource"] = ""
			source["path"] = source["storage_type"] + source["resource"] + sjc["folder"]
			source["write_mode"] = sjc["write_mode"]
			source["redistribution"] = sjc["redistribution"]
			source["partition_name"] = sjc["partition_name"]
			source["partition_date_format"] = sjc["partition_date_format"]
			source["format"] = sjc["format"]
			source["number_of_partitions"] = sjc["number_of_partitions"]
			source["read_start_date"] = parseDatePattern(item["read_start_date"], processDate)
			source["read_end_date"] = parseDatePattern(item["read_end_date"], processDate)
			source["read_mode"] = item["read_mode"]
			source["search_tolerance"] = int(item["search_tolerance"])
			sourceTables[tableName] = source

	if("keytab" in jobArguments.keys() and "principal" in jobArguments.keys()):
		print(f'creating session with keytab : {jobArguments.get("keytab")} and principal: {jobArguments.get("principal")}')
		sparkConfig["spark.kerberos.keytab"] = jobArguments["keytab"]
		sparkConfig["spark.kerberos.principal"] = jobArguments["principal"]

	initializeSparkSession()

def initializeSparkSession():
	print("SETTING UP SparkSession")
	global sparkSession
	try:
		print(f'sparkConfig: {sparkConfig}')
		if "local" not in jobArguments["master"]:
			sparkSession = SparkSession.builder \
								.appName(appName) \
								.master(jobArguments["master"]) \
								.config(map=sparkConfig) \
								.enableHiveSupport() \
								.getOrCreate()
		else:
			sparkSession = SparkSession.builder \
								.appName(appName) \
								.getOrCreate()
	except Exception as e:
		raise e

def readSourceTableParquet(s3_path):
	print("PASOK SA BANGA!")
	try:
		df = sparkSession.read.parquet(s3_path)
		return df
	except Exception as e:
		print(e)

def loadSourceTable(**kwargs):
	dataStorage = None
	schema = None
	readOptions = {}
	processDate = None
	columnFilter = None
	if("dataStorage" in kwargs.keys()):
		dataStorage = kwargs.get("dataStorage")
	if("schema" in kwargs.keys()):
		schema = kwargs.get("schema")
	if("readOptions" in kwargs.keys()):
		readOptions = kwargs.get("readOptions")
	if("processDate" in kwargs.keys()):
		processDate = kwargs.get("processDate")
	if("columnFilter" in kwargs.keys()):
		columnFilter = kwargs.get("columnFilter")
		
	return readSourceTable(dataStorage, schema, readOptions, processDate, columnFilter)

def readSourceTable(dataStorage, schema, readOptions, processDate, columnFilter):
	sparkSession = getSparkSession()
	if(schema == None):
		schema = StructType([])
	else:
		readOptions['customSchema'] = schema
	columns = schema
	print(f'dataStorage[235]: {str(dataStorage)}')
	sourceTableOption = sourceTableOptions.get(dataStorage.get("table_name"))
	if(sourceTableOption == None):
		sourceTableOption = {}
	df = sparkSession.createDataFrame([], schema=columns)

	if "local" not in jobArguments["master"]:
		options = {**sparkDefaultOptions, **sourceTableOption, **readOptions}
	else:
		options = {**sourceTableOption, **readOptions}

	if (dataStorage.get("format").upper().startswith("GOOGLE")):
		# Implement reading from Google Sheets
		df = xgservice(dataStorage=dataStorage, readOptions=readOptions, schema=schema, sparkSession=sparkSession).processRequest()
	elif (dataStorage.get("format").upper() == "API"):
		mode = readOptions.get("mode", "default")
		if(mode == "ntlm"):
			source_datastorage = {}
			source_datastorage["base_url"] = readOptions.get("source_base_url")
			source_datastorage["headers"] = readOptions.get("source_headers")
			source_datastorage["method"] = readOptions.get("source_method", "GET")

			auth_user = readOptions.get("source_auth_user")
			auth_password = readOptions.get("source_auth_password")
			source_datastorage["auth"] = HttpNtlmAuth(auth_user, auth_password)
			
			response_key = readOptions.get("source_response_key", "value")
			
			#print all source_datastorage keys and values
			print(f"Source Storage: {source_datastorage}")

			ar_response = APIReader(args=source_datastorage).fetch_data()
			
			return ar_response
		else:
			token_datastorage = {}
			token_datastorage["base_url"] = readOptions.get("token_base_url")
			token_datastorage["auth"] = readOptions.get("token_auth")
			token_datastorage["headers"] = readOptions.get("token_headers")
			token_datastorage["method"] = readOptions.get("token_method", "GET")
			token_key_name = readOptions.get("token_key_name", "token")

			#print all token_datastorage keys and values
			print(f"Token Data Storage: {token_datastorage}")

			ar_response = APIReader(args=token_datastorage).fetch_data()	
			
			#print ar_response
			print(f"ar_response[token_datastorage]: {str(ar_response)}")

			source_datastorage = {}
			source_datastorage["base_url"] = readOptions.get("source_base_url")
			source_datastorage["auth"] = readOptions.get("source_auth")
			source_datastorage["method"] = readOptions.get("source_method", "GET")
			source_datastorage["headers"] = readOptions.get("source_headers")
			source_datastorage["key"] = f"Bearer {ar_response.get(token_key_name)}"
			response_key = readOptions.get("source_response_key", "value")

			#print all source_datastorage keys and values
			print(f"Source Storage: {source_datastorage}")

			ar_response = APIReader(args=source_datastorage).fetch_data()
			#print ar_response
			# print(f"ar_response[source_datastorage]: {str(ar_response)}")	

			df = APIReader(spark_session=sparkSession, data=ar_response.get(response_key)).process_data(df=df)
		
	else:	# for non-api formats
		if("basePath" not in options.keys()):
			options["basePath"] = dataStorage["path"]
		print("Reading : " + options["basePath"])

		if("read_start_date" not in dataStorage.keys() or "read_end_date" not in dataStorage.keys() or processDate == None):
			if(len(schema) == 0):
				df = sparkSession.read.options(**options).format(dataStorage["format"]).load()
			else:
				df = sparkSession.read.format(dataStorage["format"]).options(**options).schema(schema).load()
		elif(dataStorage.get("format").upper() == "JDBC"):
			print("READING SOURCE as JDBC")
			if(len(schema) > 0):
				print("READING WITH SCHEMA")
				df = sparkSession.read.schema(schema).format(dataStorage["format"]).options(**options).load()
			else:
				print("READING WITHOUT SCHEMA")
				df = sparkSession.read.format(dataStorage["format"]).options(**options).load()
		else:
			if(dataStorage["read_mode"] == "STRICT"):
				df = readTableInStrictMode(dataStorage, schema, options, df)
			if(dataStorage["read_mode"] == "SEARCH"):
				df = readTableInSearchMode(dataStorage, schema, options, df)
			if(dataStorage["read_mode"] == "LAX"):
				df = readTableInLaxMode(dataStorage, schema, options, df)

		if(columnFilter != None):
			df = df.filter(columnFilter)

		options.pop("basePath")

	return df

def generateTablePaths(dataStorage, options):
	generatedTablePaths = []

	if(dataStorage["read_start_date"] != None and dataStorage["read_end_date"] != None and dataStorage["read_start_date"] != dataStorage["read_end_date"]):
		print("GENERATING PATHS FOR TABLE: " + dataStorage["table_name"])
	else:
		print("GENERATING PATH FOR TABLE: " + dataStorage["table_name"])

	startDate = dataStorage.get("read_start_date").strftime("%Y-%m-%d")

	if(dataStorage.get("read_mode") == "SEARCH"):
		endDate = (dataStorage.get("read_start_date") - timedelta(days=int(dataStorage.get("search_tolerance")))).strftime("%Y-%m-%d")
	else:
		endDate = dataStorage.get("read_end_date").strftime("%Y-%m-%d")

	sdate = dt(int(startDate.split("-")[0]), \
				int(startDate.split("-")[1]), \
				int(startDate.split("-")[2]))   # start date
	edate = dt(int(endDate.split("-")[0]), \
				int(endDate.split("-")[1]), \
				int(endDate.split("-")[2]))   # end date

	dateRange = pd.date_range(edate, sdate)
	for date in pd.date_range(edate, sdate):
		generatedTablePaths.append(produceTablePath(dataStorage) + date.strftime(dataStorage["partition_date_format"]) + "/")

	return reversed(generatedTablePaths)

def readTableInStrictMode(dataStorage, schema, options, dataFrame):
	print("Reading Table in STRICT mode.")
	sparkSession = getSparkSession()
	paths = generateTablePaths(dataStorage, options)
	for path in paths:
		if "excel" in dataStorage.get('format'):
			path = path + options.get('filename')
		print("READING Partition(Strict): " + path)
		try:
			if(len(schema) == 0):
				df = sparkSession.read.options(**options) \
						.format(dataStorage["format"]).load(path)
			else:
				df = sparkSession.read.options(**options) \
						.format(dataStorage["format"]).schema(schema).load(path)
		except Exception as e:
			raise Exception("Partition Path:" + path + " does not exist")
		if(dataFrame.rdd.isEmpty()):
			dataFrame = df
		else:
			dataFrame = dataFrame.union(df)
	return dataFrame

def readTableInSearchMode(dataStorage, schema, options, dataFrame):
	print("Reading Table in SEARCH mode.")
	sparkSession = getSparkSession()
	sdate = dataStorage["read_start_date"] - \
			pd.DateOffset(days=dataStorage["search_tolerance"])
	print(f"format: {dataStorage.get('format')}")
	for path in generateTablePaths(dataStorage, options):
		if "excel" in dataStorage.get('format'):
			path = path + options.get('filename')
		print("READING Partition(Search): " + path)
		try:
			if(len(schema) == 0):
				dataFrame = sparkSession.read\
						.format(dataStorage["format"])\
						.options(**options).load(path)
			else:
				dataFrame = sparkSession.read.options(**options) \
						.format(dataStorage["format"]).schema(schema).load(path)
			if(dataFrame != None):
				print("Path: " + path + " exists.")
				break
		except Exception as e:
			print("Path: " + path + " does not exist.")
	return dataFrame

def readTableInLaxMode(dataStorage, schema, options, dataFrame):
	print("Reading Table in LAX mode.")
	sparkSession = getSparkSession()
	if(dataStorage.get("read_start_date") == "*" and dataStorage.get("read_end_date") == "*"):
		if(len(schema) == 0):
			dataFrame = sparkSession.read.options(**options) \
				.format(dataStorage["format"]).load(dataStorage["path"])
		else:
			dataFrame = sparkSession.read.options(**options) \
				.format(dataStorage["format"]).schema(schema).load(dataStorage["path"])
	else:
		paths = generateTablePaths(dataStorage, options)
		for path in paths:
			if "excel" in dataStorage.get('format'):
				path = path + options.get('filename')
			print("READING Partition(LAX): " + path)
			try:
				if(len(schema) == 0):
					df = sparkSession.read.options(**options) \
							.format(dataStorage["format"]).load(path)
				else:
					df = sparkSession.read.options(**options) \
							.format(dataStorage["format"]).schema(schema).load(path)
			except Exception as e:
				print("Partition Path: " + path + " does not exist")
			if(dataFrame.rdd.isEmpty()):
				dataFrame = df
			else:
				dataFrame = dataFrame.union(df)
	return dataFrame

def writeToTargetTable(targetTable, writeDate):
	print("WRITING TO TargetTable")
	path = getDefaultJobProperties("target.table.path") + getWriteOptionProperties("partition") + "=" + writeDate + "/"
	if(getWriteOptionProperties("redistribution").upper() == "REPARTITION"):
		targetTable = targetTable.repartition(int(getWriteOptionProperties("num.partition")))
	if(getWriteOptionProperties("redistribution").upper() == "COALESCE"):
		targetTable = targetTable.coalesce(int(getWriteOptionProperties("num.partition")))
	else:
		targetTable = targetTable.repartition(int(getWriteOptionProperties("num.partition")))

	try:
		targetTable.write.format(getWriteOptionProperties("format")) \
			.mode(getWriteOptionProperties("mode")) \
			.save(path)
	except Exception as e:
		raise e
		
	print("Done writing to target table")

def writeToTargetTable(dataStorage, dataset, writeOptions, jdbcWriteOptions, processDate):
	if "local" not in getJobArguments(key="master"):
		options = {**sparkDefaultOptions, **writeOptions}
	else:
		options = {**writeOptions}

	path = ""
	if(dataStorage.get("format").upper() == "JDBC"):
		jdbcOptions["dbtable"] = dataStorage.get("table_name")
		options = {**jdbcOptions, **jdbcWriteOptions, **options}
		print("WRITING as JDBC")
		dataset.write.options(**options).format(dataStorage.get("format"))\
			.mode(dataStorage.get("write_mode")).save()
	else:
		path = generateTablePath(dataStorage)

		if(dataStorage.get("redistribution").upper() == "REPARTITION"):
			dataset = dataset.repartition(int(dataStorage.get("number_of_partitions")))
		else:
			dataset = dataset.coalesce(int(dataStorage.get("number_of_partitions")))

		lower_case_dict = {k.lower(): v for k, v in options.items()}
		if("filename" in lower_case_dict):
			path = path + options.get("filename")
		print("WRITING to path: " + path)
		print(f"options: {str(options)}")
		dataset.write.options(**options).format(dataStorage.get("format"))\
			.mode(dataStorage.get("write_mode")).save(path)
	
	print(f"targetTableDataStorage: {str(dataStorage)}")

def writeData(**kwargs):
	#TODO - implement targettable options
	global writeDate
	global targetTable
	global targetTableOptions
	global targetTableDataset
	global jdbcOptions
	global startTimeEpoch
	global startTimestamp
	global endTimestamp
	global endTimeEpoch
	if("targetTable" in kwargs.keys()):
		thisTargetTable = kwargs.get("targetTable")
		targetTable = thisTargetTable	
	if("writeDate" in kwargs.keys()):
		thisWriteDate = kwargs.get("writeDate")
		writeDate = thisWriteDate	
	if("targetTableOptions" in kwargs.keys()):
		thisTargetTableOptions = kwargs.get("targetTableOptions")
		targetTableOptions = {**targetTableOptions, **thisTargetTableOptions}
	if("targetTableDataset" in kwargs.keys()):
		thisTargetTableDataset = kwargs.get("targetTableDataset")
		targetTableDataset = thisTargetTableDataset
	if("jdbcOptions" in kwargs.keys()):
		thisJdbcOptions = kwargs.get("jdbcOptions")
		jdbcOptions = {**jdbcOptions, **thisJdbcOptions}
	writeToTargetTable(targetTable, targetTableDataset, targetTableOptions, jdbcOptions, writeDate)
	endTimestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	endTimeEpoch = time.perf_counter()
	elapsed_time = endTimeEpoch - startTimeEpoch
	print(f"start : {startTimestamp} | {startTimeEpoch}")
	print(f"end : {endTimestamp} | {endTimeEpoch}")
	print(f"elapsed : {elapsed_time}")

def doJobAuditing(data):
	smtp_server = auditOptions["server"]
	port =  auditOptions["port"]
	sender_email =  auditOptions["sender"]
	password =  auditOptions["password"]
	maskname =  auditOptions["maskname"]
	subject =  "Audit Report: " + appName.upper()
	recipients =  data["recipients"]
	email_recipients = recipients.split(",")
	email_content =  data["content"]

	# Create a secure SSL context
	msg = MIMEMultipart("alternative")
	msg['Subject'] = subject
	msg['From'] = formataddr((maskname, sender_email))
	msg['To'] = ", ".join(email_recipients)
	html_part = MIMEText(email_content, "html")
	msg.attach(html_part)

	context = ssl.create_default_context()
	with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
		server.login(sender_email, password)
		server.sendmail(sender_email, email_recipients, msg.as_string())

def getDefaultJobProperties(propertyName):
	return getSpecificJobProperties("default", propertyName)

def getWriteOptionProperties(propertyName):
	return getSpecificJobProperties("write_options", propertyName)

def getJdbcOptionProperties(propertyName):
	return getSpecificJobProperties("jdbc_options", propertyName)

def getJobAuditProperties(propertyName):
	return getSpecificJobProperties("job_audit", propertyName)

def getSpecificJobProperties(groupName, propertyName):
	return jobProperties.get(groupName, propertyName)

def getDictionarFromProperties(groupName):
	return dict(jobProperties.items(groupName))

def getSparkSession():
	return sparkSession

def setTargetTableDataset(targetTable):
	global targetTableDataset
	if isinstance(targetTable, pd.DataFrame):
		targetTableDataset = sparkSession.createDataFrame(targetTable)
	elif isinstance(targetTable, SparkDataFrame):
		targetTableDataset = targetTable
	else:
		raise TypeError("Unknown DataFrame type.")

def setProcessDate(process_date):
	global processDate
	processDate = process_date

def tearDown():
	print("stopping sparkSession")
	sparkSession.stop

def executeSubProcess(options):
	print("------------ExecuteSubProcess---------------")
	print("options: " + str(options))
	return subprocess.run([options["command"]], \
				shell=options["shell"], \
				capture_output=options["capture_output"], \
				text=options["text"]).stdout

def handlePostWrite():
	print("------------HandlePostWrite---------------")
	global endTimestamp
	command = "ps aux | grep -w " + auditOptions.get("user") + "| " \
				+ "grep -w " + appName + "| " \
				+ "grep -v grep | cut -d' ' -f4"
	print("command: " + command)
	auditOptions["command"] = command
	auditOptions["shell"] = True
	auditOptions["capture_output"] = True
	auditOptions["text"] = True
	usages = executeSubProcess(auditOptions).split()
	usage = "Memory Usage: " + usages[0] + "<br />" + "CPU Usage :" + usages[1]
	count = targetTableDataset.count()
	content = auditOptions["content"].replace("#COUNT#", str(count)).replace("#PROCESS_DATE#", processDate.strftime("%Y-%m-%d")) \
				.replace("#USAGE#", usage)
	auditOptions["content"] = content
	doJobAuditing(auditOptions)
	endTimestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	usageAPI = str(getDefaultJobProperties("usage.logs")) \
				+ "?name=Spark-Dev" \
				+ "&job_name=" + quote(appName) \
				+ "&cpu_usage=" + quote(str(usages[1])) \
				+ "&memory_usage=" + quote(str(usages[0])) \
				+ "&message=" + quote("Audit Report") \
				+ "&start=" + quote(str(startTimestamp)) \
				+ "&end=" + quote(str(endTimestamp))
	callAPI(apiURL=usageAPI, httpMode="post")

def getJobArguments(**kwargs):
	key = kwargs.get("key")
	if(key != None and len(key) > 0):
		return jobArguments.get(key)
	else:
		return jobArguments

def getCustomJobArguments(**kwargs):
	key = kwargs.get("key")
	if(key != None and len(key) > 0):
		return customJobArgs.get(key)
	else:
		return customJobArgs

def getSourceTables(**kwargs):
	key = kwargs.get("key")
	if(key != None and len(key) > 0):
		return sourceTables.get(key)
	else:
		return sourceTables

def getTargetTable():
	return targetTable

def setTargetTable(dataStorage):
	global targetTable
	targetTable = dataStorage

def getProcessDate():
	return processDate

def getWriteDate():
	return writeDate

def generateTablePath(dataStorage):
    partition_names = dataStorage["partition_name"].lower().split(",")
    partition_format = dataStorage["partition_date_format"]
    # Use processDate or writeDate as needed; here, using writeDate for consistency
    partition_value = writeDate.strftime(partition_format)

    # Build partition path dynamically
    partition_path = ""
    for pname in partition_names:
        partition_path += f"{pname}={partition_value}/"

    path = f'{dataStorage["path"]}{partition_path}'
    return path

def produceTablePath(dataStorage):
	path = dataStorage["path"] + dataStorage["partition_name"].lower() + "="
	return path

def parseBaseDate(datePattern, processDate):
	if(datePattern == "*"):
		return None
	else:
		if("CURRENT_DATE" not in datePattern and "TRANSACTION_DATE" not in datePattern):
			raise Exception("date pattern must start with CURRENT_DATE or TRANSACTION_DATE")
		elif("CURRENT_DATE" in datePattern and "TRANSACTION_DATE" in datePattern):
			raise Exception("date pattern must start with CURRENT_DATE or TRANSACTION_DATE")
		else:
			if("TRANSACTION_DATE" in datePattern):
				return processDate
			return datetime.datetime.now()

def parseDatePattern(datePattern, processDate):
	derivedDate = datetime.datetime.now()

	if("TRANSACTION" in datePattern or "CURRENT" in datePattern):
		derivedDate = parseBaseDate(datePattern, processDate)
		if(derivedDate == None):
			return None
	else:
		derivedDate = datetime.datetime.now().strftime(datePattern)

	pattern = re.findall("PLUS_YEARS_\\d+", datePattern)
	if(len(pattern) > 0):
		offset = int(pattern[0].split("_")[2])
		derivedDate = pd.to_datetime(datetime.datetime.now()) \
						+ pd.DateOffset(years=offset)

	pattern = re.findall("MINUS_YEARS_\\d+", datePattern)
	if(len(pattern) > 0):
		offset = int(pattern[0].split("_")[2])
		derivedDate = pd.to_datetime(datetime.datetime.now()) \
						- pd.DateOffset(years=offset)

	pattern = re.findall("PLUS_MONTHS_\\d+", datePattern)
	if(len(pattern) > 0):
		offset = int(pattern[0].split("_")[2])
		derivedDate = pd.to_datetime(datetime.datetime.now()) \
						+ pd.DateOffset(months=offset)

	pattern = re.findall("MINUS_MONTHS_\\d+", datePattern)
	if(len(pattern) > 0):
		offset = int(pattern[0].split("_")[2])
		derivedDate = pd.to_datetime(datetime.datetime.now()) \
						- pd.DateOffset(months=offset)

	pattern = re.findall("PLUS_WEEKS_\\d+", datePattern)
	if(len(pattern) > 0):
		offset = int(pattern[0].split("_")[2])
		derivedDate = pd.to_datetime(datetime.datetime.now()) \
						+ pd.DateOffset(weeks=offset)

	pattern = re.findall("MINUS_WEEKS_\\d+", datePattern)
	if(len(pattern) > 0):
		offset = int(pattern[0].split("_")[2])
		derivedDate = pd.to_datetime(datetime.datetime.now()) \
						- pd.DateOffset(weeks=offset)

	if("FIRST" in datePattern):
		derivedDate = derivedDate.replace(day=1)
	if("LAST" in datePattern):
		derivedDate = derivedDate + relativedelta(day=31)

	pattern = re.findall("PLUS_DAYS_\\d+", datePattern)
	if(len(pattern) > 0):
		offset = int(pattern[0].split("_")[2])
		derivedDate = pd.to_datetime(datetime.datetime.now()) \
						+ pd.DateOffset(days=offset)

	pattern = re.findall("MINUS_DAYS_\\d+", datePattern)
	if(len(pattern) > 0):
		offset = int(pattern[0].split("_")[2])
		derivedDate = pd.to_datetime(datetime.datetime.now()) \
						- pd.DateOffset(days=offset)

	return derivedDate

def getSparkDefaultOptions():
	return sparkDefaultOptions

def setWriteDate(thisDate:datetime):
	global writeDate
	writeDate = thisDate

def callAPI(**kwargs):
	apiURL = kwargs.get("apiURL", None)
	httpMode = kwargs.get("httpMode", None)
	body = kwargs.get("body", None)
	headerToken = getDefaultJobProperties("api.token")
	if(httpMode.upper() == "GET"):
		return requests.get(apiURL, headers={'Authorization': headerToken})
	elif(httpMode.upper() == "POST"):
		if(body != None and len(body) > 0):
			return requests.post(apiURL, headers={'Authorization': headerToken}, json=body)
		else:
			return requests.post(apiURL, headers={'Authorization': headerToken})
	else:
		raise Exception("Invalid httpMode.")

def getSourceTableOption(tableName):
	return sourceTableOptions.get(tableName)

def getTargetTableOption():
	return targetTableOptions

def setTargetTableOption(options):
	targetTableOptions = {**options, **targetTableOptions}

def getOptionalParams(**kwargs):
	key = kwargs.get("key", None)
	if(key != None and len(key) > 0):
		return optionalParams.get(key)
	else:
		return optionalParams

def getSparkConfig(**kwargs):
	key = kwargs.get("key", None)
	if(key != None and len(key) > 0):
		return sparkConfig.get(key)
	else:
		return sparkConfig
	
def uploadToS3(**kwargs):
	# Replace these placeholder values with your own
	filePath = kwargs.get("filePath")
	filePaths = kwargs.get("filePaths")
	bucketName = kwargs.get("bucketName")
	subDirectory = kwargs.get("subDirectory")
	extraArgs = kwargs.get("contentType")

	if(extraArgs == None or extraArgs.strip() == ''):
		extraArgs = "application/octet-stream"
	if(subDirectory == None):
		subDirectory = targetTable.get("folder") \
			+ targetTable.get("partition_name").lower() + "=" \
			+ writeDate.strftime(targetTable.get("partition_date_format")) \
			+ "/"
			
	if(bucketName == None):
		bucketName = targetTable.get("resource")
	if(filePaths == None):
		filePaths = []
		filePaths.append(filePath)

	sparkConfig = getSparkConfig()
	ACCESS_KEY = sparkConfig.get("session.spark.hadoop.fs.s3a.access.key")
	SECRET_KEY = sparkConfig.get("session.spark.hadoop.fs.s3a.secret.key")
	partitionName = getTargetTable().get("partition_name")

	# Create an S3 client
	s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

	# Loop through file names and upload each file to S3
	for filename in filePaths:
		# Get the file path of the file
		abspath = os.path.abspath(filename)
		# Get the base name of the file
		theFile = os.path.basename(filename)

		# Get the content type of the file
		content_type = mimetypes.guess_type(filename)[0]
		resource = f"{subDirectory}{theFile}"

		# Upload the file to S3 in the specified subdirectory
		with open(filename, 'rb') as f:
			s3.upload_fileobj(f, bucketName, resource, ExtraArgs={'ContentType': extraArgs})
	
def sendEmail(**kwargs):
	print("kwargs: " + str(kwargs))
	smtp = auditOptions["server"]
	smtp_port =  auditOptions["port"]
	from_email =  auditOptions["sender"]
	email_password =  auditOptions["password"]

	subject = str(kwargs.get("subject"))
	to_email = kwargs.get("to_email")
	message = str(kwargs.get("message"))
	files = kwargs.get("files")
	rename = kwargs.get("rename")
	bodyContentType = kwargs.get("body_content_type")
	msg = MIMEMultipart()
	msg['Subject'] = subject
	msg['From'] = from_email
	msg['To'] = ', '.join(to_email)

	# Attach message
	if(bodyContentType != None and len(bodyContentType) > 0):
		body = MIMEText(message, bodyContentType)
	else:
		body = MIMEText(message)

	msg.attach(body)

	#check if email has attachment
	if(files != None and len(files) > 0):
		# Attach Documents
		if(rename == None):
			for file in files:
				with open(file, 'rb') as attachment_file:
					part = MIMEBase('application', "octet-stream")
					part.set_payload(open(file, "rb").read())
				encoders.encode_base64(part)
				part.add_header('Content-Disposition', 'attachment', filename=str(file))  
				msg.attach(part)
		else:
			for file, new_name in zip(files, rename):
				with open(file, 'rb') as attachment_file:
					part = MIMEBase('application', "octet-stream")
					part.set_payload(open(file, "rb").read())
				encoders.encode_base64(part)
				part.add_header('Content-Disposition', f'attachment; filename= {new_name}')  
				msg.attach(part)

	# Send email
	s = smtplib.SMTP(smtp, smtp_port)
	s.ehlo()
	s.starttls()
	s.login(from_email, email_password)
	s.sendmail(from_email, to_email, msg.as_string())
	s.quit()

def fetchFileFromS3():
	# Set the AWS access key and secret key
	ACCESS_KEY = sparkConfig.get("session.spark.hadoop.fs.s3a.access.key")
	SECRET_KEY = sparkConfig.get("session.spark.hadoop.fs.s3a.secret.key")

	# Set the name of the S3 bucket, the subdirectory, and the file to be loaded
	bucket_name = targetTable.get("resource")
	subdirectory_name = targetTable.get("folder")[1:-1] \
		+ targetTable.get("partition_name").lower() + "=" \
		+ writeDate.strftime(targetTable.get("partition_date_format"))

	# Get the directory of the current file
	current_dir = os.path.dirname(os.path.realpath(__file__))
	
	# Create the path to the subdirectory
	subdir_path = os.path.join(current_dir, "private")
	
	# Create the subdirectory if it doesn't exist
	if not os.path.exists(subdir_path):
		os.makedirs(subdir_path)

	# Create an S3 resource
	s3 = boto3.resource('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)
	bucket = s3.Bucket(bucket_name)
	for obj in bucket.objects.filter(Prefix=subdirectory_name):
		file_key = obj.key
		file_name = file_key.split('/')[-1]
		index_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "private")
		local_file_path = os.path.join(index_path, file_name)
		bucket.download_file(file_key, local_file_path)

	return f'{local_file_path}'

def tapChatGPT(**kwargs):
	OPENAI_API_KEY = kwargs.get("key")
	DATA_STATISTICS = kwargs.get("statistics")
	QUERY = kwargs.get("query")
	MODEL = kwargs.get("model")
	MAX_TOKENS = kwargs.get("maxTokens")

	if(MODEL == None):
		MODEL = "gpt-3.5-turbo-instruct"

	if(MAX_TOKENS == None):
		MAX_TOKENS = 100

	# Define the API endpoint
	url = f'https://api.openai.com/v1/chat/completions'

	messages = [
		{"role": "system", "content": "You are a helpful assistant."},
		{"role": "user", "content": f'{QUERY}: {DATA_STATISTICS}'},
	]

	# Define the headers for the API request
	headers = {
				"Content-Type": "application/json",
				"Authorization": "Bearer " + OPENAI_API_KEY
			}

	# Define the data for the API request
	data = {
			"model": MODEL,
			"messages": messages,
			"max_tokens": MAX_TOKENS
		}

	# Make the API request
	response = requests.post(url, headers=headers, data=json.dumps(data))

	# Get the response text
	response_text = response.json()

	return response_text

def updateS3Permission(**kwargs):
	permission = kwargs.get("permission")
	subdirectory_name = kwargs.get("subDirectory")

	if(permission == None):
		permission = 'public-read'
	if(subdirectory_name == None):
		subdirectory_name = targetTable.get("folder") \
			+ targetTable.get("partition_name").lower() + "=" \
			+ writeDate.strftime(targetTable.get("partition_date_format"))

	# Set the AWS access key and secret key
	ACCESS_KEY = sparkConfig.get("session.spark.hadoop.fs.s3a.access.key")
	SECRET_KEY = sparkConfig.get("session.spark.hadoop.fs.s3a.secret.key")
	s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

	# Set the name of the S3 bucket, the subdirectory, and the file to be loaded
	bucket_name = targetTable.get("resource")

	# Use paginator to handle buckets with many objects
	paginator = s3.get_paginator('list_objects_v2')
	pages = paginator.paginate(Bucket=bucket_name, Prefix=subdirectory_name)

	# Iterate over each page and each object in the page
	for page in pages:
		if 'Contents' in page:
			for obj in page['Contents']:
				s3.put_object_acl(ACL=permission, Bucket=bucket_name, Key=obj['Key'])
				print(f"Permissions updated for {obj['Key']}")

def generateDataQualityReport(**kwargs):
	title = kwargs.get("dq_title")
	filePath = kwargs.get("dq_file_path")
	df = kwargs.get("dq_df")
	message = kwargs.get("dq_message")

	if(title == None):
		title = f'{targetTable.get("database_name")}_{targetTable.get("table_name")}'
	if(filePath == None):
		filePath = f'{os.path.dirname(__file__)}/{targetTable.get("database_name")}_{targetTable.get("table_name")}.html'
	if(df == None):
		df = targetTableDataset.toPandas()
	if(message == None):
		message = 'Hi'
	
	# integration with XAIL DQ reporting library
	report = DataReport(df=df,
		report_name=title, 
		file_path=f'{filePath}')
	report.to_file()

	# read the HTML file
	with open(filePath, 'r') as f:
		html_content = f.read()
	recipients = auditOptions.get("recipients")
	if(optionalParams.get("audit.recipients") != None and len(optionalParams.get("audit.recipients")) > 0):
		recipients = f'{recipients},optionalParams.get("audit.recipients")'
	emailRecipients = recipients.split(",")
	files = [filePath]
	rename = [f'{title}.html']
	sendEmail(subject=f'[{scope_env}]Data Profile[{title}]-{processDate}', message=message, from_email=auditOptions.get("sender"), 
		to_email=emailRecipients, files=files, rename=rename)

def createHiveTable():
	hive_database = targetTable.get("database_name")
	hive_table = targetTable.get("table_name")
	partition_column = targetTable.get("partition_name").lower()
	partition_value = processDate.strftime(targetTable.get("partition_date_format"))
	hdfs_path = generateWritePath()

	# Generate column types based on DataFrame schema
	column_types = ", ".join([f"{col} {get_hive_data_type(data_type)}" for col, data_type in targetTableDataset.dtypes])

	hiveContext = HiveContext(sparkSession)
	hive_query = f"""
				CREATE TABLE IF NOT EXISTS `{hive_table}` (
					{column_types}
				) 
				PARTITIONED BY ({partition_column} string)
				STORED AS PARQUET
				LOCATION '{targetTable["path"]}
				USING hive'
			"""
	print(f'hive query(create if not exist): {hive_query}')
	hiveContext.sql(hive_query)

def registerPartition(**kwargs):
	print(f'******************** Registering Partition to Hive *******************')
	mode = kwargs.get("mode")
	hive_database = targetTable.get("database_name")
	hive_table = targetTable.get("table_name")
	partition_name = kwargs.get("partition_name")
	partition_names = kwargs.get("partition_names")  # Expecting list of tuples: [("col1", "val1"), ("col2", "val2")]
	partition_location = kwargs.get("partition_location", generateWritePath())

	if mode is None:
		mode = ""

	if partition_name is None and partition_names is None:
		partition_name = targetTable.get("partition_name").lower()
		partition_spec = f"{partition_name}='{writeDate.strftime(targetTable.get('partition_date_format'))}'"
	else:
		if partition_name or partition_names is None:
			partition_spec = f"{partition_name}='{writeDate.strftime(targetTable.get('partition_date_format'))}'"
		else:
			# Build partition spec string for multiple columns using the tuple list
			if partition_names:
				partition_spec = ",".join([f"{col}='{val}'" for col, val in partition_names])
			else:
				# fallback to old logic if not provided
				partition_cols = targetTable.get("partition_name").lower().split(",")
				partition_format = targetTable.get("partition_date_format")
				partition_value = processDate.strftime(partition_format)
				partition_spec = ",".join([f"{col}='{partition_value}'" for col in partition_cols])

	hive_query = f"""
		ALTER TABLE {hive_database}.{hive_table}
		ADD IF NOT EXISTS PARTITION ({partition_spec})
		LOCATION '{partition_location}'
	"""
	print(f'hive query(add partition): {hive_query}')
	sparkSession.sql(hive_query)
	# hiveContext = HiveContext(sparkSession)
	# hiveContext.sql(hive_query)

def generateWritePath():
	partition_names = targetTable["partition_name"].lower().split(",")
	partition_format = targetTable["partition_date_format"]
	partition_value = writeDate.strftime(partition_format)

	# Build partition path dynamically
	partition_path = ""
	for pname in partition_names:
		partition_path += f"{pname}={partition_value}/"
	
	path = f'{targetTable["path"]}{partition_path}'
	return path

def generateWritePaths():
    """
    Generate partition paths dynamically:
    - First partition uses writeDate
    - Succeeding partitions use unique values from targetTableDataset columns
    Returns a list of partition paths.
    """
    partition_names = targetTable["partition_name"].lower().split(",")
    partition_format = targetTable["partition_date_format"]
    base_path = targetTable["path"]
    paths = []

    if len(partition_names) == 1:
        # Only one partition column, use writeDate
        partition_value = writeDate.strftime(partition_format)
        partition_path = f"{partition_names[0]}={partition_value}/"
        paths.append(f"{base_path}{partition_path}")
    else:
        # First partition uses writeDate, others use DataFrame columns
        first_partition = partition_names[0]
        other_partitions = partition_names[1:]
        first_value = writeDate.strftime(partition_format)

        # Get unique combinations of the other partition columns
        unique_combinations = (
            targetTableDataset
            .select(*other_partitions)
            .dropDuplicates()
            .toPandas()
            .to_dict(orient="records")
        )

        for combo in unique_combinations:
            partition_path = f"{first_partition}={first_value}/"
            for col in other_partitions:
                partition_path += f"{col}={combo[col]}/"
            paths.append(f"{base_path}{partition_path}")

    return paths

# Function to map PySpark data types to Hive data types
def get_hive_data_type(spark_data_type):
	result = ""
	if isinstance(spark_data_type, StringType):
		result = "STRING"
	elif isinstance(spark_data_type, IntegerType):
		result = "INT"
	elif isinstance(spark_data_type, DoubleType):
		result = "DOUBLE"
	elif isinstance(spark_data_type, TimestampType):
		result = "TIMESTAMP"
	else:
		# Add more mappings for other data types as needed
		result = "STRING"
	return result