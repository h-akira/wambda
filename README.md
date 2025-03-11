# HADS
## Overview
HADS (h-akira AWS Develop with Serverless) is a framework to develop serverless web applications on AWS.  
Although this framework is a successor to [HAD](https://github.com/h-akira/had), 
there are some cases where it is recommended to continue using HAD because the philosophy is very different.
## Philosophy
- Use SAM
- One Lambda
- Static files are distributed from S3
- Test Locally
- Like Django
## Structure
The AWS configuration for a system built using HADS is shown below. 
Only Lambda and API Gateway are created directly by HADS. 
Although S3 is not created, 
it is possible to synchronize static files using HADS commands.
Other resources are created separately or added to SAM's template.yaml by developper.
![structure](images/structure.png)  
The Lambda program structure is shown below. 
It is similar to Django, with urls.py, views.py, and template at its core. 
The same Lambda is called from API Gateway regardless of the path. 
When the handler is executed, the view function is passed by the routing function after the initial settings and authentication.
The view function is executed in the handler and the result is returned.
![lambda](images/lambda.png)  

## Usage
Comming soon...
## Development Schedule
The following features will be added ad later date:
- Genarete SAM and other templates
