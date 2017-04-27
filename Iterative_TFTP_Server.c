/*

	Alejandro Aguilar Esteban
	159007645
	aa1363
	Iterative TFTP Server

*/


#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <sys/wait.h>
#include <signal.h>
#include <stdarg.h>
#include <assert.h>
#include <fcntl.h>

#define BLOCK_SIZE 516
#define HEADER_SIZE 4
#define DATA_SIZE 512

const int READ_OP = 1;
const int WRITE_OP = 2;
const int DATA_OP = 3;
const int ACK_OP = 4;
const int ERROR_OP = 5;

const int FILE_ERROR = 1;
const int ACCESS_ERROR = 2;
const int ILLEGALOP_ERROR = 4;

struct RRQ {
	short op;
	char filename[DATA_SIZE - 1];
	short byte;
	char mode[DATA_SIZE - 1];

};

struct Data {
	short op;
	short block_nr;
	char bytes[DATA_SIZE];
};

struct Error {
	short op;
	short error_code;
	char err_msg[DATA_SIZE];
};


void err_msg(){
	perror("TFTP_Server.c");
	exit(0);
}


void print_info(char* RT,char* mode, char * filename, in_addr_t sin_addr, in_port_t sin_port) {
	/* Print request type, mode,file name, ip address */
	printf("%s %s file \"%s\" requested from %d.%d.%d.%d:%hu\n", RT, mode, filename, (sin_addr >> 24) & 0xff, (sin_addr >> 16) & 0xff, (sin_addr >> 8) & 0xff, (sin_addr) & 0xff,sin_port);
}

int main(int argc, char *argv[]){

	/*** Structs ***/
	struct sockaddr_in server;
	struct sockaddr_in client;
	struct RRQ request;
	struct Error err;
	struct Data datablock;
	struct Data ackblock;
	struct Error * errblock = (struct Error*) &ackblock;

	/*** Declarations ***/
	int sfd, optval=1;
	short port;
	char* directory = argv[2];
	char resolved_directory[PATH_MAX];
	long long realret = (long long) realpath(directory, resolved_directory);
	ssize_t ret;
	char RRQ [] ="RRQ";
	char RT[3];
	char filepath[PATH_MAX];
	char resolved_filepath[PATH_MAX];


	if (argc < 3) {
		fprintf(stderr, "Usage: %s <port number> <Path>\n", argv[0]);
		exit(0);
	}

	/* Parse the port number and data path */
	sscanf(argv[1], "%hd", &port);
	if(realret == 0) {
		err_msg();
	}



	/*** UDP socket ***/
	if((sfd = socket(AF_INET,SOCK_DGRAM,0)) < 0){
		err_msg();
	}
	
	/* Eliminates "Address already in use" error from bind. */
	if (setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, (const void *)&optval , sizeof(int)) < 0){
		err_msg();
	}


	/*** set memset with constant byte ***/
	memset(&server, 0, sizeof(server));
	

	/*** Setting Network byte order ***/
	server.sin_family = AF_INET;
	server.sin_addr.s_addr = htonl(INADDR_ANY);
	server.sin_port = htons(port);
	
	

	/**** Bind ****/
	if(ret = bind(sfd,(struct sockaddr*)&server,sizeof(server)) < 0){
		err_msg();
	}
	printf("/********** Server Enabled ********/\n\n");
	printf("Port: %hu\nPath: %s\n\n", port, resolved_directory);
	for (;;) {
		
	int bytes_read = 0;
	int next_block = 1;
	int read = 1;
		memset(&request, 0, sizeof(request));
		socklen_t len = (socklen_t) sizeof(client);

		/*** Preparing error opcode ***/
		memset(&err, 0, sizeof(err));
		err.op = htons(ERROR_OP);

		/*** Read request from client ***/
		if((ret = recvfrom(sfd, (void *) &request, sizeof(request), 0, (struct sockaddr *) &client, &len)) < 0){
			err_msg();
		}

		/*** Provide error message if trying to client trying to upload ***/
		if(ntohs(request.op) == WRITE_OP) {
			err.error_code = htons(ACCESS_ERROR);
			strncpy(err.err_msg, "Error! Sever does not support Uploading", sizeof(err.err_msg));
			if((ret = sendto(sfd, &err, strlen(err.err_msg) + HEADER_SIZE, 0, (struct sockaddr *) &client, len)) < 0){
				err_msg();
			}
			continue;
		}

		/*** Provide message if unexpected contact ***/
		if(ntohs(request.op) != READ_OP && ntohs(request.op) != WRITE_OP ) {
			err.error_code = htons(ILLEGALOP_ERROR);
			strncpy(err.err_msg, "Error! Serve does not support this type of request", sizeof(err.err_msg));
			if((ret = sendto(sfd, &err, strlen(err.err_msg) + HEADER_SIZE, 0, (struct sockaddr*) &client, len)) < 0){
				err_msg();
			}
			continue;
		}

		/*** Get RRQ and mode ***/
		if(ntohs(request.op) == READ_OP){
			strncpy(RT,RRQ,sizeof(RRQ));
			strncpy(request.mode, "octet", sizeof(request.mode));
		}

		/*** catcating path with filename ***/
		memset(&filepath, 0, sizeof(filepath));
		strcpy(filepath, directory);
		strcat(filepath, "/");
		strcat(filepath, request.filename);
		

		/*** making sure only requested path is to be used ***/
		if((realret = (long long) realpath(filepath, resolved_filepath)) < 0){
			err_msg();
		}

		/*** Start at input directory. ***/
		if (strncmp(resolved_filepath, resolved_directory, strlen(resolved_directory))) {
			err.error_code = htons(ACCESS_ERROR);
			strncpy(err.err_msg, "You are not authorized to access this file!", sizeof(err.err_msg));
			if((ret = sendto(sfd, &err, strlen(err.err_msg) + HEADER_SIZE, 0, (struct sockaddr *) &client, len)) < 0){
				perror("Unauthorized request");
			}
			continue;
		}

		/*** Open the requested file ***/
		FILE *Fp = fopen(resolved_filepath, "rb");
		if (!Fp) {
			err.error_code = htons(FILE_ERROR);
			strncpy(err.err_msg, "The requested file could not be opened/found!", sizeof(err.err_msg));
			if((ret = sendto(sfd, &err, strlen(err.err_msg) + HEADER_SIZE, 0, (struct sockaddr *) &client, len)) < 0 ){
				err_msg();
			}
			continue;
		}
		
		char* mode = strchr(request.filename, '\0') + 1; 
		/*** Print information ***/
		print_info(RT,request.mode, request.filename, ntohl(client.sin_addr.s_addr), client.sin_port);

		
		memset(&datablock, 0, sizeof(datablock));
		memset(&ackblock, 0, sizeof(ackblock));

		
		for (;;) {
			/*** Set up datablock op code and blocknumber ***/
			datablock.op = htons(DATA_OP);
			datablock.block_nr = htons(next_block);
			/*** Resend last block again if an error occurred ***/
			if (read) {
				memset(datablock.bytes, 0, DATA_SIZE);
				bytes_read = fread(&datablock.bytes, 1, DATA_SIZE, Fp);
			}
			read = 0;
			/*** Send the datablock ***/
			if((ret = sendto(sfd, &datablock, (size_t) bytes_read + HEADER_SIZE, 0,(struct sockaddr *) &client, len)) < 0){
				err_msg();
			}

			memset(&ackblock, 0, sizeof(ackblock));
			/*** receive acknowledgement ***/
			if((ret = recvfrom(sfd, (void *) &ackblock, BLOCK_SIZE,0, (struct sockaddr *) &client, &len)) < 0){
				err_msg();
			}

			/*** Display block number on client */
			ackblock.op = ntohs(ackblock.op);
			ackblock.block_nr = ntohs(ackblock.block_nr);

			/*** If block is transmitted then increment block counter and set read to true ***/
			if (ackblock.op == ACK_OP && ackblock.block_nr == next_block) {
				next_block++;
				read = 1;
				/*** break if file transfer is successful and is less than 512 bytes */
				if (bytes_read < DATA_SIZE) {
					break;
				}
			} else if (ackblock.op == ERROR_OP) {
				errblock->err_msg[DATA_SIZE - 1] = '\0';
				printf("ERROR block from client with nr: %d err_code: %d msg: %s\n", next_block, errblock->error_code, errblock->err_msg);
				fflush(stdout);
				break;
			}
		}

		fclose(Fp);
		printf("%s\n", "File transfer success");
		fflush(stdout);
	}
	
}

