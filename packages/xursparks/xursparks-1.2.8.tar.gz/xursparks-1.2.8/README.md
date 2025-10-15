# Xursparks - XAIL's Apache Spark Framework

## Overview

Welcome to the Xurpas AI Lab (XAIL) department's Apache Spark Framework. This framework is specifically designed to help XAIL developers implement Extract, Transform, Load (ETL) processes seamlessly and uniformly. Additionally, it includes integration capabilities with the Data Management and Configuration Tool (DMCT) to streamline your data workflows.

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Usage](#usage)
    - [Setting Up Your Spark Application](#setting-up-your-spark-application)
    - [ETL Process Implementation](#etl-process-implementation)
    - [Integration with DMCT](#integration-with-dmct)
5. [Best Practices](#best-practices)
6. [Contributing](#contributing)
7. [Support](#support)
8. [License](#license)

## Introduction

This framework aims to provide a robust and standardized approach for XAIL developers to handle ETL processes using Apache Spark. By leveraging this framework, you can ensure that your data pipelines are efficient, maintainable, and easily integrable with the DMCT tool.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Apache Spark 3.0 or higher
- Python 3.10 or higher
- Access to the DMCT tool and relevant API keys

## Installation

To use framework, follow these steps:

1. install xursparks in python env:
```
pip install xursparks
```

2. check if properly installed"
```
pip list
```

## Usage
Setting Up Your Spark Application
To start using the framework, create ETL Job as follows:
```
import xursparks

xursparks.initialize(args)

```

## ETL Process Implementation
The framework provides predefined templates and utility functions to facilitate your ETL processes.
```
sourceTables = xursparks.getSourceTables()
sourceDataStorage = sourceTables.get("scheduled_manhours_ELE")
processDate = xursparks.getProcessDate()
sourceDataset = xursparks.loadSourceTable(dataStorage=sourceDataStorage,
												processDate=processDate)
```

## Integration with DMCT
To integrate with the DMCT tool, ensure you have the required configurations set up in your application.properties file:
```
[default]
usage.logs=<usage logs>
global.config=<dmct global config api>
job.context=<dmct job context api>
api.token="dmct api token"
```

## Best Practices
Always validate your data at each stage of the ETL process.
- Leverage Spark's in-built functions and avoid excessive use of UDFs (User Defined Functions) for better performance.
- Ensure proper error handling and logging to facilitate debugging.
- Keep your ETL jobs modular and maintainable by adhering to the single responsibility principle.

## Contributing
We welcome contributions to improve this framework. Please refer to the CONTRIBUTING.md file for guidelines on how to get started.

## Support
If you encounter any issues or have questions, please reach out to the XAIL support team at support@xail.com.

## License
This project is licensed under the Apache License 2.0. See the LICENSE file for details.


--------------------------------------------------------------------------------

## Running Xursparks Job

* SPARK-SUBMIT
```
spark-submit XurSparkSMain.py \
--master=local[*] \
--client-id=trami-data-folder \
--target-table=talentsolutions.candidate_reports \
--process-date=2023-05-24 \
--properties-file=job-application.properties \
--switch=1
```

* Hadoop Sir Andy Setp
```
python AiLabsCandidatesDatamart.py \
--master=local[*] \
--deploy-mode=cluster \
--client-id=trami-data-folder \
--target-table=ailabs.candidates_transformed \
--process-date=2023-11-15 \
--properties-file=job-application.properties \
--switch=1
```

* Hadoop
```
spark-submit \
--name AiLabsCandidatesDatamart \
--master yarn \
--jars aws-java-sdk-bundle-1.12.262.jar,hadoop-aws-3.3.4.jar \
--conf spark.yarn.dist.files=job-application.properties \
AiLabsCandidatesDatamart.py \
--keytab=hive.keytab \
--principal=hive/hdfscluster.local@HDFSCLUSTER.LOCAL \
--master=yarn \
--deploy-mode=cluster \
--client-id=trami-data-folder \
--target-table=ailabs.candidates_transformed \
--process-date=2023-11-16 \
--properties-file=job-application.properties \
--switch=1
```

* Hadoop 3.3.2
``` 
spark-submit \
--name AiLabsCandidatesDatamart \
--master yarn \
--keytab hive.keytab \
--principal hive/hdfscluster.local@HDFSCLUSTER.LOCAL \
--jars aws-java-sdk-bundle-1.12.262.jar,hadoop-aws-3.3.4.jar,hive-jdbc-3.1.3.jar \
--conf spark.yarn.dist.files=job-application.properties \
AiLabsCandidatesDatamart.py \
--keytab=hive.keytab \
--principal=hive/hdfscluster.local@HDFSCLUSTER.LOCAL \
--master=yarn \
--deploy-mode=client \
--client-id=trami-data-folder \
--target-table=ailabs.candidates_transformed \
--process-date=2023-11-17 \
--properties-file=job-application.properties \
--switch=1
```

* Hadoop testhdfs 3.3.2
``` 
spark-submit \
--name HdfsTest \
--master yarn \
--deploy-mode client \
--keytab hive.keytab \
--principal hive/hdfscluster.local@HDFSCLUSTER.LOCAL \
--jars aws-java-sdk-bundle-1.12.262.jar,hadoop-aws-3.3.4.jar \
--conf spark.yarn.dist.files=job-application.properties \
--driver-memory 4g \
--executor-memory 4g \
--executor-cores 2 \
HdfsTest.py \
--keytab=hive.keytab \
--principal=hive/hdfscluster.local@HDFSCLUSTER.LOCAL \
--master=yarn \
--deploy-mode=cluster \
--client-id=trami-data-folder \
--target-table=ailabs.candidates_transformed \
--process-date=2023-11-16 \
--properties-file=job-application.properties \
--switch=1
```

* Hadoop
```
spark-submit \
--name AiLabsCandidatesDatamart \
--master yarn \
--jars aws-java-sdk-bundle-1.12.262.jar,hadoop-aws-3.3.4.jar,hive-jdbc-3.1.3.jar \
--conf spark.yarn.dist.files=job-application.properties \
AiLabsCandidatesDatamart.py \
--master=yarn \
--deploy-mode=client \
--client-id=trami-data-folder \
--target-table=ailabs.candidates_transformed \
--process-date=2023-11-19 \
--properties-file=job-application.properties \
--switch=1
```

* Hadoop Employees
``` 
spark-submit \
--name AiLabsEmployeeDatamart \
--master yarn \
--keytab hive.keytab \
--principal hive/hdfscluster.local@HDFSCLUSTER.LOCAL \
--jars aws-java-sdk-bundle-1.12.262.jar,hadoop-aws-3.3.4.jar,hive-jdbc-3.1.3.jar,spark-excel_2.12-3.5.0_0.20.1.jar \
--conf spark.yarn.dist.files=job-application.properties \
AiLabsEmployeeDatamart.py \
--keytab=hive.keytab \
--principal=hive/hdfscluster.local@HDFSCLUSTER.LOCAL \
--master=yarn \
--deploy-mode=client \
--client-id=trami-data-folder \
--target-table=ailab.employees \
--process-date=2023-11-30 \
--properties-file=job-application.properties \
--switch=1
```

* Hadoop Candidates
``` 
spark-submit \
--name AiLabsHdfsDatamart \
--master yarn \
--keytab hive.keytab \
--principal hive/hdfscluster.local@HDFSCLUSTER.LOCAL \
--jars aws-java-sdk-bundle-1.12.262.jar,hadoop-aws-3.3.4.jar,hive-jdbc-3.1.3.jar,spark-excel_2.12-3.5.0_0.20.1.jar \
--conf spark.yarn.dist.files=job-application.properties \
AiLabsHdfsDatamart.py \
--keytab=hive.keytab \
--principal=hive/hdfscluster.local@HDFSCLUSTER.LOCAL \
--master=yarn \
--deploy-mode=client \
--client-id=trami-data-folder \
--target-table=ailab.candidates_transformed_hdfs \
--process-date=2023-11-19 \
--properties-file=job-application.properties \
--switch=1
```