# Alternate PowerShell Hosts

## Metadata


|               |    |
|:--------------|:---|
| id            | WIN-190815181010 |
| author        | Roberto Rodriguez @Cyb3rWard0g |
| creation date | 2019/08/15 |
| platform      | Windows |
| playbook link | WIN-190410151110 |
        

## Technical Description
Adversaries can abuse alternate signed PowerShell Hosts to evade application whitelisting solutions that block powershell.exe and naive logging based upon traditional PowerShell hosts.
Characteristics of a PowerShell host (Matt Graeber @mattifestation) >
* These binaries are almost always C#/.NET .exes/.dlls
* These binaries have System.Management.Automation.dll as a referenced assembly
* These may not always be “built in” binaries

## Hypothesis
Adversaries might be leveraging alternate PowerShell Hosts to execute PowerShell evading traditional PowerShell detections that look for powershell.exe in my environment.

## Analytics

### Initialize Analytics Engine

from openhunt.mordorutils import *
spark = get_spark()

### Download & Process Mordor File

mordor_file = "https://raw.githubusercontent.com/OTRF/mordor/master/datasets/small/windows/execution/empire_invoke_psremoting.tar.gz"
registerMordorSQLTable(spark, mordor_file, "mordorTable")

### Analytic I


| FP Rate  | Log Channel | Description   |
| :--------| :-----------| :-------------|
| Medium       | ['PowerShell']          | Within the classic PowerShell log, event ID 400 indicates when a new PowerShell host process has started. Excluding PowerShell.exe is a good way to find alternate PowerShell hosts            |
            

df = spark.sql(
    '''
SELECT `@timestamp`, computer_name, channel
FROM mordorTable
WHERE (channel = "Microsoft-Windows-PowerShell/Operational" OR channel = "Windows PowerShell")
    AND (event_id = 400 OR event_id = 4103)
    AND NOT message LIKE "%Host Application%powershell%"
    '''
)
df.show(10,False)

### Analytic II


| FP Rate  | Log Channel | Description   |
| :--------| :-----------| :-------------|
| Medium       | ['Microsoft-Windows-Sysmon/Operational']          | Looking for processes loading a specific PowerShell DLL is a very effective way to document the use of PowerShell in your environment            |
            

df = spark.sql(
    '''
SELECT `@timestamp`, computer_name, Image, Description
FROM mordorTable
WHERE channel = "Microsoft-Windows-Sysmon/Operational"
    AND event_id = 7
    AND (lower(Description) = "system.management.automation" OR lower(ImageLoaded) LIKE "%system.management.automation%")
    AND NOT Image LIKE "%powershell.exe"
    '''
)
df.show(10,False)

### Analytic III


| FP Rate  | Log Channel | Description   |
| :--------| :-----------| :-------------|
| Low       | ['Microsoft-Windows-Sysmon/Operational']          | Monitoring for PSHost* pipes is another interesting way to find other alternate PowerShell hosts in your environment.            |
            

df = spark.sql(
    '''
SELECT `@timestamp`, computer_name, Image, PipeName
FROM mordorTable
WHERE channel = "Microsoft-Windows-Sysmon/Operational"
    AND event_id = 17
    AND lower(PipeName) LIKE "\\\pshost%"
    AND NOT Image LIKE "%powershell.exe"
    '''
)
df.show(10,False)

## Detection Blindspots


## Hunter Notes
* Explore the data produced in your lab environment with the analytics above and document what normal looks like from alternate powershell hosts. Then, take your findings and explore your production environment.
* You can also run the script below named PowerShellHostFinder.ps1 by Matt Graber and audit PS host binaries in your environment.

## Hunt Output

| Category | Type | Name     |
| :--------| :----| :--------|
| signature | SIGMA | [powershell_alternate_powershell_hosts](https://github.com/OTRF/ThreatHunter-Playbook/tree/master/signatures/sigma/powershell_alternate_powershell_hosts.yml) |
| signature | SIGMA | [sysmon_alternate_powershell_hosts_moduleload](https://github.com/OTRF/ThreatHunter-Playbook/tree/master/signatures/sigma/sysmon_alternate_powershell_hosts_moduleload.yml) |
| signature | SIGMA | [sysmon_alternate_powershell_hosts_pipe](https://github.com/OTRF/ThreatHunter-Playbook/tree/master/signatures/sigma/sysmon_alternate_powershell_hosts_pipe.yml) |

## References
* https://twitter.com/mattifestation/status/971840487882506240
* https://gist.githubusercontent.com/mattifestation/fcae777470f1bdeb9e4b32f93c245fd3/raw/abbe79c660829ab9aad58581baf681655f6ba305/PowerShellHostFinder.ps1