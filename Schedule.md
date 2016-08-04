Full mesh schedule for placement.

There are six endpoints involved in the schedule

 1. Beihang Univeristy, China  (Mickey)
 2. CNIC, China (idpl.elab)
 3. University of Wisconsin (komatsu)
 4. University of California, San Diego 1G  (murpa)
 5. Calit2, UC San Diego 10G (flashio-osg)
 6. Physics, UC San Diego 40G (mongo)

The first four run condor schedd (scheduler) services. Each of the sites
runs tests every hour. For simplicity (except for murpa, which also schedules
tests from flashio-osg), each host schedules a test as the client (sender)

**Mickey**
<p> subdirectory for experiments: `/home/zwzhang/placement4`

| EXPERIMENT | DST_HOST             | File Size | Minute   |
|------------|----------------------|:---------:|:--------:|
| buaa2cnic  | idpl.elab.cnic.cn    | 100MB     | 0        |
| buaa2wisc    | komatsu.chtc.wisc.edu| 10MB      | 10       |
| buaa2ucsd    | murpa.rocksclusters.org| 10MB    | 30       |

**idpl.elab**
<p> subdirectory for experiments: `/home/zwzhang/mesh/placement`

| EXPERIMENT | DST_HOST             | File Size | Minute   |
|------------|----------------------|:---------:|:--------:|
| cnic2buaa  | mickey.buaa.edu.cn   | 100MB     | 5        |
| cnic2wisc    | komatsu.chtc.wisc.edu| 10MB      | 30       |
| cnic2ucsd    | murpa.rocksclusters.org| 10MB    | 10       |

**komatsu.chtc.wisc.edu**
<p> subdirectory for experiments: `/home/phil/mesh/placement`

| EXPERIMENT | DST_HOST             | File Size | Minute   |
|------------|----------------------|:---------:|:--------:|
| wisc2buaa    | mickey.buaa.edu.cn                | 10MB     |   20    |
| wisc2cnic    | idpl.elab.cnic.cn                 | 10MB     |   40    |
| wisc2ucsd | murpa.rocksclusters.org           | 100MB    |   0     |
| wisc2calit      | flashio-osg.calit2.optiputer.net  | 100MB    |   50    |

**murpa.rocksclusters.org**  (calit is flashio-osg.calit2.optiputer.net)
<p> subdirectory for experiments: `/home/phil/mesh/placement`

| EXPERIMENT | DST_HOST             | File Size | Minute   |
|------------|----------------------|:---------:|:--------:|
| ucsd2buaa    | mickey.buaa.edu.cn                | 10MB     |   40    |
| ucsd2cnic    | idpl.elab.cnic.cn                 | 10MB     |   20    |
| ucsd2wisc      | komatsu.chtc.wisc.edu             | 100MB    |    5    |
| calit2wisc      | komatsu.chtc.wisc.edu             | 100MB    |   55    |
| calit2physics   | mongo.mayer.optiputer.net         | 1G       |   15    | 
| physics2calit      | flashio-osg.calit2.optiputer.net  | 1G       |   30    |

*Note:* calit2physics and physics2calit2 are internal to UCSD on a 10G link. Scheduled by murpa. should be non-conflicting

The web portal to display the full mesh experiment results can be found: [IDPL Portal](http://mickey.buaa.edu.cn:11401/highcharts/table.html)
