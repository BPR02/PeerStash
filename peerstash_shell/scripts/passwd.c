#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char ** const argv) {
	setuid(0);
	system("/peerstash/scripts/passwd.sh");
	return 0;
}
