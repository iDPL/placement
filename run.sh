#!/bin/sh

CONDOR_CHIRP=`condor_config_val LIBEXEC`/condor_chirp
MD5SUM=/usr/bin/md5sum
DATE=/bin/date
EXPR=/usr/bin/expr
IPERF=/usr/bin/iperf
DD=/bin/dd
GREP=/bin/grep
TIMEOUT=600
SERVER=0


# For file tests
TEST_FILE=test-file
TEST_FILE_SIZE_MB=200
TEST_FILE_SIZE=`$EXPR 1024 '*' 1024 '*' $TEST_FILE_SIZE_MB`
DD_BLOCK_SIZE=8192


if [ -e /opt/iperf/bin/iperf ]; then
	IPERF=/opt/iperf/bin/iperf
fi


# Allow this entire script to run for only a certain amount of time
allow_time()
{
   ( echo timer allowing $1 seconds for execution
     sleep $1
     echo timer expired...killing
     KILLPID=`ps --ppid $$ | grep iperf | cut -f 1 -d ' '`
     echo iperf pid is $KILLPID
     [ $KILLPID -ne 0 ] && kill -TERM $KILLPID
     ps $$ > /dev/null
     if [ ! $? ] ; then
       kill -TERM -- -$$
       kill -TERM $$
     fi
   ) &
}

timeout_handler()
{
   echo allowable time of $TIMEOUT for execution exceeded.
   exit 1
}

get_job_attr_blocking() {
    #echo "Waiting for attribute $1" 1>&2
    let countdown=$TIMEOUT
    while [ $countdown -gt 0 ] 
    do
        Value=`$CONDOR_CHIRP get_job_attr $1`
        if [ $? -ne 0 ]; then
            echo "Chirp is broken!" 1>&2
            return 1
        fi
        if [ "$Value" != "UNDEFINED" -a "$Value" != '"UNDEFINED"' ]; then
            echo "$Value" | tr -d '"'
            return 0
        fi
	let countdown=countdown-2
        sleep 2
    done
    ## we timed out of the loop
    echo "timed out Waiting for attribute $1" 1>&2
    if [ $SERVER -ne 0 ]; then
	cleanup_server
    else
	cleanup_client
    fi
    return 2
}

get_timestamp() {
    $DATE +%s
}

checksum() {
    $MD5SUM $1 | awk '{print $1}'
}

cleanup_client()
{
	echo cleanup_client
}
server_active()
{
    $CONDOR_CHIRP set_job_attr JobServerActive ACTIVE 
}
cleanup_server()
{

    $CONDOR_CHIRP set_job_attr JobServerActive \"UNDEFINED\"
    $CONDOR_CHIRP set_job_attr JobServerAddress \"UNDEFINED\"
    $CONDOR_CHIRP set_job_attr IPerfAddress \"UNDEFINED\"
    $CONDOR_CHIRP set_job_attr IPerfDone \"UNDEFINED\"
}
synchronize_server() {
    # Wipe our attributes
    # (This actually sets these to the string "UNDEFINED", but close enough

    $CONDOR_CHIRP set_job_attr JobServerAddress \"UNDEFINED\"
    $CONDOR_CHIRP set_job_attr IPerfAddress \"UNDEFINED\"

    ADDRESS_EXPIRES=`$EXPR \`get_timestamp\` +  $LEASE_DURATION`
    $CONDOR_CHIRP set_job_attr ServerReady $ADDRESS_EXPIRES
    server_active
    return 0;
}

synchronize_client() {
    ServerReady=`get_job_attr_blocking JobServerActive`
    if [ $? -ne 0 ]; then
       echo "Unable to get JobServerActive"
       return 1
    fi
    return 0;
}

receive_server() {
    echo "I'm the server receiver"

    # Start netcat listening on an ephemeral port (0 means kernel picks port)
    #    It will wait for a connection, then write that data to output_file

    nc -d -l 0 > "$DESTINATION" &

    # pid of the nc running in the background
    NCPID=$!

    # Sleep a bit to ensure nc is running
    sleep 2

    # parse the actual port selected from netstat output
    NCPORT=`
        netstat -t -a -p 2>/dev/null |
        grep " $NCPID/nc" |
        awk -F: '{print $2}' | awk '{print $1}'`

    echo "Listening on $HOSTNAME $NCPORT"
    $CONDOR_CHIRP set_job_attr JobServerAddress \"${HOSTNAME}\ ${NCPORT}\"

    # Do other server things here...
    #sleep 60

    EXPECTED_CHECKSUM=`get_job_attr_blocking FileChecksum`
    if [ $? -ne 0 ]; then
        echo "Chirp is broken"
        return 1
    fi

    while /bin/kill -0 $NCPID >/dev/null 2>&1
    do
        ls -l $DESTINATION
        sleep 1
    done

    CHECKSUM=`checksum $DESTINATION`
    if [ "$EXPECTED_CHECKSUM" != "$CHECKSUM" ]; then
        echo "File did not arrive intact! Sender claimed checksum is $EXPECTED_CHECKSUM, but I calculated $CHECKSUM";
        return 1
    fi;

    echo "$EXPECTED_CHECKSUM==$CHECKSUM";

    $CONDOR_CHIRP set_job_attr ResultFileReceived TRUE

    return 0
}

send_client() {
    echo "I'm the client/sender"
    
    JobServerAddress=`get_job_attr_blocking JobServerAddress`
    if [ $? -ne 0 ]; then
        echo "Chirp is broken"
        return 1
    fi
    echo "JobServerAddress: $JobServerAddress";

    host=`echo $JobServerAddress | awk '{print $1}'`
    port=`echo $JobServerAddress | awk '{print $2}'`

    CHECKSUM=`checksum $FILE_TO_SEND`
    echo "Checksum: $CHECKSUM"

    echo "Sending to $host $port"
    echo "nc $host $port < $FILE_TO_SEND"
    ls -l $FILE_TO_SEND
    TIME_START=`get_timestamp`
    nc $host $port < $FILE_TO_SEND
    echo "Sent $?"
    TIME_END=`get_timestamp`
    $CONDOR_CHIRP set_job_attr ResultTimeStart "$TIME_START"
    $CONDOR_CHIRP set_job_attr ResultTimeEnd "$TIME_END"

    echo "Posting that transfer is done, checksum is $CHECKSUM" 
    $CONDOR_CHIRP set_job_attr FileChecksum "\"$CHECKSUM\""

    $CONDOR_CHIRP ulog "File transfer successful: $SENDER:$FILE_TO_SEND -> $RECEIVER:$DESTINATION. Started at $TIME_START, finished at $TIME_END. Checksum is $CHECKSUM"

    return 0
}



net_tests_server() {
    $IPERF --server --port 0 2>&1 1> iperf-server.out &
    IPERFPID=$!
    KILLPID=$IPERFPID

    # Ensure iperf is ready
    sleep 2

    IPERFPORT=`
        netstat -t -a -p 2>/dev/null |
        grep " $IPERFPID/iperf" |
        awk -F: '{print $2}' | awk '{print $1}'`
    
    echo "iperf is pid $IPERFPID listening on $HOSTNAME $IPERFPORT"

    # Clear flag before telling client to continue
    $CONDOR_CHIRP set_job_attr IPerfDone \"UNDEFINED\"
    $CONDOR_CHIRP set_job_attr IPerfAddress \"${HOSTNAME}\ ${IPERFPORT}\"

    IPERF_DONE=`get_job_attr_blocking IPerfDone`
    if [ $? -ne 0 ]; then
        echo "Chirp is broken"
        return 1
    fi
}

net_tests_client() {
    IPerfAddress=`get_job_attr_blocking IPerfAddress`
    if [ $? -ne 0 ]; then
        echo "Chirp is broken"
        return 1
    fi
    echo "IPerfAddress: $IPerfAddress";

    host=`echo $IPerfAddress | awk '{print $1}'`
    port=`echo $IPerfAddress | awk '{print $2}'`

    perf_result=`$IPERF --client $host --port $port | grep ' sec '`
    if [ $? -ne 0 ]; then
        echo "Failed to run iperf client"
        return 1
    fi

    $CONDOR_CHIRP set_job_attr IPerfDone 1

    echo "iperf results: $perf_result"
    $CONDOR_CHIRP ulog "iperf results: $perf_result"

    return 0
}


disk_test() {
    COUNT=`$EXPR $TEST_FILE_SIZE / $DD_BLOCK_SIZE`

    WRITE_RESULTS=`$DD if=/dev/zero of=$TEST_FILE bs=$DD_BLOCK_SIZE count=$COUNT 2>&1 | $GREP copied`
    READ_RESULTS=`$DD if=$TEST_FILE of=/dev/null bs=$DD_BLOCK_SIZE count=$COUNT 2>&1 | $GREP copied`

    rm $TEST_FILE

    $CONDOR_CHIRP ulog "Write test: $_CONDOR_PROCNO $HOSTNAME $WRITE_RESULTS"
    echo "Write test: $WRITE_RESULTS"
    $CONDOR_CHIRP ulog "Read test: $_CONDOR_PROCNO $HOSTNAME $READ_RESULTS"
    echo "Read test: $READ_RESULTS"
    return 0
}



SENDER="$1"
FILE_TO_SEND="$2"
RECEIVER="$3"
DESTINATION="$4"
LEASE_DURATION="$5"

if [ "$DESTINATION" = "" ]; then
    cat <<END
Usage: $0 source_host source_file destination_host destination_file
END
    exit 1
fi

HOSTNAME=`hostname`

echo "I am $HOSTNAME, node $_CONDOR_PROCNO"
echo "$SENDER $FILE_TO_SEND -> $RECEIVER $DESTINATION"


## Make sure this entire script doesn't hang indefinitely
#trap timeout_handler SIGTERM
#allow_time $TIMEOUT
#########################################################
 
# All hosts run this independently
disk_test
if [ $? -ne 0 ]; then
    echo "Failed to disk test"
    exit 1
fi

if [ $_CONDOR_PROCNO = "1" ]; then
    echo "I am the server"
    SERVER=1

    synchronize_server
    if [ $? -ne 0 ]; then
        echo "Failed to sychronize"
	cleanup_server
        exit 1
    fi

    net_tests_server
    if [ $? -ne 0 ]; then
        echo "Failed to run net tests"
	cleanup_server
        exit 1
    fi

    $CONDOR_CHIRP set_job_attr ResultsFileSent "\"$FILE_TO_SEND\""
    $CONDOR_CHIRP set_job_attr ResultsHostSend "\"$SENDER\""
    $CONDOR_CHIRP set_job_attr ResultsHostReceive "\"$RECEIVER\""

    receive_server
    RESULT=$?
    if [ $RESULT -ne 0 ]; then
        echo "Error receiving file"
    fi

    cleanup_server
elif [ $_CONDOR_PROCNO = "0" ]; then
    echo "I am the client"

    synchronize_client
    if [ $? -ne 0 ]; then
        echo "Failed to sychronize"
	cleanup_client
        exit 1
    fi

    net_tests_client
    if [ $? -ne 0 ]; then
        echo "Failed to run net tests"
	cleanup_client
        exit 1
    fi

    send_client
    RESULT=$?
    if [ $RESULT -ne 0 ]; then
        echo "Error sending file"
    fi
    cleanup_client
else
    echo "This node was not expected. Exiting immediately"
fi;
