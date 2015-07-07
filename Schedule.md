Full mesh schedule for placement.

There are five endpoints involved in the schedule

 1. Beihang Univeristy, China  (Mickey)
 2. CNIC, China (idpl.elab)
 3. University of Wisconsin (komatsu)
 4. University of California, San Diego 1G  (murpa)
 5. University of California, San Diego 10G (flashio-osg)

The first four run condor schedd (scheduler) services. Each of the sites
runs tests every hour. For simplicity (except for murpa, which also schedules
tests from flashio-osg), each host schedules a test as the client (sender)

** Mickey **

| EXPERIMENT | DST_HOST             | File Size | Minute   |
|------------|----------------------|:---------:|:--------:|
| buaa2cnic  | idpl.elab.cnic.cn    | 100MB     | 0        |
| buaa2ko    | komatsu.chtc.wisc.edu| 10MB      | 10       |
| buaa2mu    | murpa.rocksclusters.org| 10MB    | 30       |

** idpl.elab **

| EXPERIMENT | DST_HOST             | File Size | Minute   |
|------------|----------------------|:---------:|:--------:|
| cnic2buaa  | mickey.buaa.edu.cn   | 100MB     | 5        |
| cnic2ko    | komatsu.chtc.wisc.edu| 10MB      | 30       |
| cnic2mu    | murpa.rocksclusters.org| 10MB    | 10       |

** komatsu.chtc.wisc.edu **

| EXPERIMENT | DST_HOST             | File Size | Minute   |
|------------|----------------------|:---------:|:--------:|
| ko2buaa    | mickey.buaa.edu.cn                | 10MB     |   20    |
| ko2cnic    | idpl.elab.cnic.cn                 | 10MB     |   40    |
| ko2mu      | murpa.rocksclusters.org           | 100MB    |   0     |
| ko2fl      | flashio-osg.calit2.optiputer.net  | 100MB    |   50    |

** murpa.rocksclusters.org **

| EXPERIMENT | DST_HOST             | File Size | Minute   |
|------------|----------------------|:---------:|:--------:|
| mu2buaa    | mickey.buaa.edu.cn                | 10MB     |   40    |
| mu2cnic    | idpl.elab.cnic.cn                 | 10MB     |   20    |
| mu2ko      | komatsu.chtc.wisc.edu             | 100MB    |    5    |
| fl2ko      | komatsu.chtc.wisc.edu             | 100MB    |   55    |
| fl2mo      | mongo.mayer.optiputer.net         | 1G       |   15    | 
| mo2fl      | flashio-osg.calit2.optiputer.net  | 1G       |   30    |

*Note*:fl2mo and mo2fl are internal to UCSD on a 10G link. Scheduled by murpa.

