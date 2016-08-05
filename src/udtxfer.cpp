#include <cstdlib>
#include <netdb.h>
#include <fstream>
#include <iostream>
#include <cstring>
#include <stdio.h>
#include <udt.h>

/*
 * udtxfer -- send and recieve one file and exit via udt
 *
 * CLI:
 *  server side
 *		udtxfer -s -p portno -f fileToSend
 *  client side
 *		udtxfer -c dns_name_of_server -p portNo -f fileToWriteTo
 *
 * udt will transfer one file, print out performance statistics, and exit
 */

using namespace std;

void* sendfile(void*);

bool isServer = false;
char *servername = 0;
char *filename = 0;
const char *port = "0"; // any port in a storm


int main(int argc, char* argv[])
{
		//usage: udtxfer -c servername -p port -f localfile
		//usage: udtxfer -s -p port -f file_to_send

	int i = 1;
	while (i < argc) {
		if (argv[i][0] == '-') {
			switch (argv[i][1]) {
			case 'c':
				i++;
				isServer = false;
				servername = argv[i];
				break;
			case 'f':
				i++;
				filename = argv[i];
				break;
			case 'p':
				i++;
				port = argv[i];
				break;
			case 's':
				isServer = true;
				break;
			default:
				printf("Unknown option: %s\n", argv[i]);
				exit(1);
			}
			i++;
		}
	}

		// use this function to initialize the UDT library
	UDT::startup();
	UDTSOCKET fhandle;

	addrinfo hints;
	addrinfo* res;

	memset(&hints, 0, sizeof(struct addrinfo));
	hints.ai_flags = AI_PASSIVE;
	hints.ai_family = AF_INET;
	hints.ai_socktype = SOCK_STREAM;

	if (0 != getaddrinfo(NULL, port, &hints, &res)) {
		printf("illegal port number or port is busy.\n");
		return -1;
	}

		// Set up our socket and bind the local side
	UDTSOCKET serv = UDT::socket(res->ai_family, res->ai_socktype, res->ai_protocol);

	if (isServer) {
	if (UDT::ERROR == UDT::bind(serv, res->ai_addr, res->ai_addrlen)) {
		cout << "bind: " << UDT::getlasterror().getErrorMessage() << endl;
		return 0;
	}

	freeaddrinfo(res);


		UDT::listen(serv, 1);
		
			// Wait for one connection, process it, then exit
		sockaddr_storage clientaddr;
		int addrlen = sizeof(clientaddr);

		printf("Waiting for connection\n");
		if (UDT::INVALID_SOCK == (fhandle = UDT::accept(serv, (sockaddr*)&clientaddr, &addrlen))) {
			printf("error accepting\n");
			exit(0);
		}

			// and send that there file
		sendfile(new UDTSOCKET(fhandle));

	} else {
			//isClient!
		struct addrinfo *peer;
		if (0 != getaddrinfo(servername, port, &hints, &peer)) {
			printf("Can't find client address\n");
			exit(0);
		}

			// connect to the server, implict bind
		if (UDT::ERROR == UDT::connect(serv, peer->ai_addr, peer->ai_addrlen)) {
			printf("Can't connect to server: %s\n", UDT::getlasterror().getErrorMessage());
			exit(0);
		}

			// get size information
		int64_t size;

		if (UDT::ERROR == UDT::recv(serv, (char*)&size, sizeof(int64_t), 0)) {
			printf("can't get size info\n");
			exit(0);
		}
		
		if (size < 0) {
			printf("no file on server\n");
			exit(0);
		}

			// receive the file
		fstream ofs(filename, ios::out | ios::binary | ios::trunc);
		int64_t recvsize; 
		int64_t offset = 0;


		long b4 = time(0);

		if (UDT::ERROR == (recvsize = UDT::recvfile(serv, ofs, offset, size))) {
			printf("can't receive file\n");
			exit(0);
		}

		long duration = time(0) - b4;

		printf("size = %ld speed = %g Mbytes/sec\n", size, ((double)size) / (1024 * 1024) / duration);
		freeaddrinfo(peer);
	}

			// And we're done.  Clean up and exit
	UDT::close(serv);
	UDT::cleanup();
	exit(0);

}

void* sendfile(void* usocket)
{
	UDTSOCKET fhandle = *(UDTSOCKET*)usocket;
	delete (UDTSOCKET*)usocket;


		// open the file
	fstream ifs(filename, ios::in | ios::binary);

	ifs.seekg(0, ios::end);
	int64_t size = ifs.tellg();
	ifs.seekg(0, ios::beg);

		// send file size information
	if (UDT::ERROR == UDT::send(fhandle, (char*)&size, sizeof(int64_t), 0))	{
		printf("error sending file size info\n");
		return 0;
	}

	UDT::TRACEINFO trace;
	UDT::perfmon(fhandle, &trace);

		// send the file
	int64_t offset = 0;
	if (UDT::ERROR == UDT::sendfile(fhandle, ifs, offset, size)) {
		printf("error sending file\n");
		return 0;
	}

	UDT::perfmon(fhandle, &trace);
	printf("size = %ld speed = %g Mbits/sec\n", size, trace.mbpsSendRate / 8.0);

	UDT::close(fhandle);

	ifs.close();

	return 0;
}
